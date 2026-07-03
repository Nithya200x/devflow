import datetime
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

import docker
from docker.errors import DockerException, NotFound, APIError

logger = logging.getLogger(__name__)


class DockerServiceError(Exception):
    pass


class DockerService:
    def __init__(self):
        self._client: Optional[docker.DockerClient] = None
        self._connected = False
        self._server_info: Dict[str, Any] = {}
        self._event_listener: Optional[threading.Thread] = None
        self._listening = False
        self._event_callback = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        with self._lock:
            try:
                if os.getenv("DOCKER_HOST"):
                    base_url = os.getenv("DOCKER_HOST")
                    tls_config = None
                    if os.getenv("DOCKER_TLS_VERIFY", "").lower() in ("1", "true"):
                        cert_path = os.getenv("DOCKER_CERT_PATH", os.path.expanduser("~/.docker"))
                        tls_config = docker.tls.TLSConfig(
                            client_cert=(os.path.join(cert_path, "cert.pem"),
                                         os.path.join(cert_path, "key.pem")),
                            ca_cert=os.path.join(cert_path, "ca.pem"),
                            verify=True,
                        )
                    self._client = docker.DockerClient(
                        base_url=base_url,
                        tls=tls_config,
                        timeout=30,
                    )
                else:
                    self._client = docker.from_env()
                self._client.ping()
                self._server_info = self._client.info()
                self._connected = True
                logger.info(f"Docker connected: {self._server_info.get('Name', 'unknown')}")
                return True
            except DockerException as e:
                self._connected = False
                self._client = None
                logger.warning(f"Docker connection failed: {e}")
                return False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def client(self) -> Optional[docker.DockerClient]:
        return self._client

    def health_check(self) -> Dict[str, Any]:
        if not self._connected or not self._client:
            return {
                "connected": False,
                "version": "",
                "api_version": "",
                "container_count": 0,
                "image_count": 0,
            }
        try:
            self._client.ping()
            info = self._client.info()
            version = self._client.version()
            return {
                "connected": True,
                "version": version.get("Version", ""),
                "api_version": version.get("ApiVersion", ""),
                "container_count": info.get("Containers", 0),
                "image_count": info.get("Images", 0),
                "server_info": {
                    "name": info.get("Name", ""),
                    "os": info.get("OperatingSystem", ""),
                    "kernel": info.get("KernelVersion", ""),
                    "driver": info.get("Driver", ""),
                },
            }
        except (DockerException, APIError) as e:
            self._connected = False
            return {
                "connected": False,
                "error": str(e),
                "version": "",
                "api_version": "",
                "container_count": 0,
                "image_count": 0,
            }

    def list_containers(self, show_all: bool = True, filters: Dict = None) -> List[Dict[str, Any]]:
        if not self._client:
            return []
        try:
            containers = self._client.containers.list(all=show_all, filters=filters)
            return [self._inspect_container(c) for c in containers]
        except (DockerException, APIError) as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None
        try:
            container = self._client.containers.get(container_id)
            return self._inspect_container(container)
        except (DockerException, APIError, NotFound) as e:
            logger.warning(f"Container {container_id} not found: {e}")
            return None

    def _inspect_container(self, container) -> Dict[str, Any]:
        try:
            attrs = container.attrs
            state = attrs.get("State", {})
            config = attrs.get("Config", {})
            host_config = attrs.get("HostConfig", {})
            network_settings = attrs.get("NetworkSettings", {})
            mounts = attrs.get("Mounts", [])
            labels = config.get("Labels", {})
            env_vars = config.get("Env", [])
            masked_env = self._mask_secrets(env_vars)

            started_at = state.get("StartedAt", "")
            finished_at = state.get("FinishedAt", "")
            running_time = self._calc_running_time(started_at, finished_at, state.get("Status", ""))

            return {
                "container_id": container.id[:12],
                "container_name": container.name,
                "status": container.status,
                "state": state.get("Status", ""),
                "image_name": config.get("Image", ""),
                "image_id": attrs.get("Image", "")[7:19] if attrs.get("Image", "").startswith("sha256:") else attrs.get("Image", ""),
                "restart_count": state.get("RestartCount", 0),
                "exit_code": state.get("ExitCode", 0),
                "started_at": started_at,
                "finished_at": finished_at,
                "running_time_seconds": running_time,
                "health_status": state.get("Health", {}).get("Status", "") if state.get("Health") else "",
                "network_mode": host_config.get("NetworkMode", ""),
                "mounted_volumes": [
                    {
                        "source": m.get("Source", ""),
                        "destination": m.get("Destination", ""),
                        "mode": m.get("Mode", ""),
                    }
                    for m in mounts
                ],
                "labels": labels,
                "environment": masked_env,
                "ports": list(network_settings.get("Ports", {}).keys()) if network_settings.get("Ports") else [],
                "networks": list(network_settings.get("Networks", {}).keys()),
            }
        except Exception as e:
            logger.warning(f"Failed to inspect container {container.id}: {e}")
            return {"container_id": container.id[:12], "container_name": container.name, "status": container.status}

    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        timestamps: bool = True,
        stdout: bool = True,
        stderr: bool = True,
    ) -> Dict[str, Any]:
        if not self._client:
            return {"stdout": "", "stderr": "", "error": "Docker not connected"}
        try:
            container = self._client.containers.get(container_id)
            raw = container.logs(
                tail=tail,
                timestamps=timestamps,
                stdout=stdout,
                stderr=stderr,
            )
            text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
            max_chars = 50000
            if len(text) > max_chars:
                text = text[-max_chars:]
            return {"logs": text, "truncated": len(text) >= max_chars}
        except (DockerException, APIError, NotFound) as e:
            return {"logs": "", "error": str(e)}

    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        if not self._client:
            return {}
        try:
            container = self._client.containers.get(container_id)
            stats = container.stats(stream=False)
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            memory_stats = stats.get("memory_stats", {})
            networks = stats.get("networks", {})
            blkio_stats = stats.get("blkio_stats", {})

            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
            num_cpus = cpu_stats.get("online_cpus", 1)
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

            mem_usage = memory_stats.get("usage", 0)
            mem_limit = memory_stats.get("limit", 1)
            mem_percent = (mem_usage / mem_limit * 100.0) if mem_limit > 0 else 0.0

            net_rx = sum(n.get("rx_bytes", 0) for n in networks.values()) if networks else 0
            net_tx = sum(n.get("tx_bytes", 0) for n in networks.values()) if networks else 0

            blkio_read = sum(
                entry.get("value", 0) for entry in blkio_stats.get("io_service_bytes_recursive", [])
                if entry.get("op") == "read"
            )
            blkio_write = sum(
                entry.get("value", 0) for entry in blkio_stats.get("io_service_bytes_recursive", [])
                if entry.get("op") == "write"
            )

            pids = stats.get("pids_stats", {}).get("current", 0)

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_bytes": mem_usage,
                "memory_limit_bytes": mem_limit,
                "memory_percent": round(mem_percent, 2),
                "network_rx_bytes": net_rx,
                "network_tx_bytes": net_tx,
                "block_io_read_bytes": blkio_read,
                "block_io_write_bytes": blkio_write,
                "pids": pids,
            }
        except (DockerException, APIError, NotFound) as e:
            logger.warning(f"Failed to get stats for {container_id}: {e}")
            return {}

    def find_containers_by_image(self, image_name: str) -> List[Dict[str, Any]]:
        return self.list_containers(filters={"ancestor": image_name})

    def find_containers_by_label(self, key: str, value: str) -> List[Dict[str, Any]]:
        return self.list_containers(filters={"label": f"{key}={value}"})

    def subscribe_events(self, callback):
        self._event_callback = callback
        if not self._listening:
            self._listening = True
            self._event_listener = threading.Thread(target=self._event_loop, daemon=True)
            self._event_listener.start()
            logger.info("Docker event listener started")

    def _event_loop(self):
        while self._listening:
            try:
                if not self._client:
                    logger.info("Docker client not available, reconnecting...")
                    self.connect()
                    if not self._client:
                        time.sleep(5)
                        continue
                for event in self._client.events(decode=True):
                    if not self._listening:
                        break
                    try:
                        self._process_event(event)
                    except Exception as e:
                        logger.debug(f"Docker event processing error: {e}")
            except (DockerException, APIError) as e:
                logger.warning(f"Docker event stream error: {e}")
                self._connected = False
                self._client = None
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Docker event loop error: {e}")
                time.sleep(5)

    def _process_event(self, event: Dict[str, Any]):
        if not self._event_callback:
            return
        event_type = event.get("Type", "")
        action = event.get("Action", "")
        actor = event.get("Actor", {})
        actor_attrs = actor.get("Attributes", {})
        container_name = actor_attrs.get("name", "")
        image = actor_attrs.get("image", "")
        exit_code = actor_attrs.get("exitCode", "")
        container_id = actor.get("ID", "")[:12]

        if event_type != "container":
            return

        data = {
            "container_id": container_id,
            "container_name": container_name,
            "image": image,
            "action": action,
            "exit_code": exit_code,
            "timestamp": event.get("time", 0),
        }

        if action in ("die", "destroy", "kill"):
            try:
                ec = int(exit_code) if exit_code else 0
            except (ValueError, TypeError):
                ec = 0
            if ec != 0:
                data["exit_code"] = ec
                data["reason"] = "exited_with_error"
            self._event_callback("container_stopped", data)

        elif action in ("restart", "start"):
            self._event_callback("container_started", data)

        elif action == "health_status":
            health_status = actor_attrs.get("healthStatus", "")
            if health_status == "unhealthy":
                data["reason"] = "unhealthy"
                self._event_callback("container_unhealthy", data)

        elif action == "oom":
            data["reason"] = "oom_killed"
            self._event_callback("container_oomkilled", data)

    def stop_listener(self):
        self._listening = False
        if self._event_listener and self._event_listener.is_alive():
            self._event_listener.join(timeout=3)

    @staticmethod
    def _calc_running_time(started_at: str, finished_at: str, status: str) -> float:
        if not started_at or status in ("exited", "created"):
            return 0.0
        try:
            start = DockerService._parse_docker_time(started_at)
            now = datetime.datetime.now(datetime.timezone.utc)
            if status in ("running",):
                return (now - start).total_seconds()
            if finished_at:
                end = DockerService._parse_docker_time(finished_at)
                return (end - start).total_seconds()
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _mask_secrets(env_vars: List[str]) -> Dict[str, str]:
        secret_keys = {"TOKEN", "SECRET", "PASSWORD", "PASS", "KEY", "API_KEY", "ACCESS_KEY"}
        result = {}
        for entry in env_vars:
            if "=" not in entry:
                continue
            key, value = entry.split("=", 1)
            if any(s in key.upper() for s in secret_keys):
                value = "***MASKED***"
            result[key] = value
        return result

    def get_all_stats(self) -> Dict[str, Any]:
        containers = self.list_containers(show_all=True)
        running = [c for c in containers if c.get("status") == "running"]
        stopped = [c for c in containers if c.get("status") == "exited"]
        total_cpu = 0.0
        total_mem = 0.0
        for c in running:
            stats = self.get_container_stats(c["container_id"])
            total_cpu += stats.get("cpu_percent", 0)
            total_mem += stats.get("memory_percent", 0)
        return {
            "containers": containers,
            "running_count": len(running),
            "stopped_count": len(stopped),
            "total_count": len(containers),
            "total_cpu_percent": round(total_cpu, 2),
            "total_memory_percent": round(total_mem / max(len(running), 1), 2),
        }


    @staticmethod
    def _parse_docker_time(time_str: str) -> datetime.datetime:
        if not time_str:
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            if "." in time_str:
                return datetime.datetime.strptime(time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
            return datetime.datetime.strptime(time_str.split("Z")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
        except (ValueError, IndexError):
            return datetime.datetime.now(datetime.timezone.utc)
