import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

from utils.time import to_iso
from utils.environment import make_service_status, get_environment_display, is_cloud

import kubernetes
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesServiceError(Exception):
    pass


class KubernetesService:
    def __init__(self):
        self._core: Optional[client.CoreV1Api] = None
        self._apps: Optional[client.AppsV1Api] = None
        self._connected = False
        self._cluster_info: Dict[str, Any] = {}
        self._watcher: Optional[threading.Thread] = None
        self._watching = False
        self._event_callback = None

    def connect(self) -> bool:
        try:
            kubeconfig = os.getenv("KUBECONFIG", "")
            if kubeconfig:
                config.load_kube_config(config_file=kubeconfig)
                logger.info(f"Kubernetes loaded kubeconfig: {kubeconfig}")
            else:
                try:
                    config.load_incluster_config()
                    logger.info("Kubernetes loaded in-cluster config")
                except config.ConfigException:
                    config.load_kube_config()
                    logger.info("Kubernetes loaded default kubeconfig")

            self._core = client.CoreV1Api()
            self._apps = client.AppsV1Api()

            version = client.VersionApi().get_code()

            cluster_name = ""
            try:
                contexts, current = config.list_kube_config_contexts()
                cluster_name = current.get("context", {}).get("cluster", "")
            except Exception:
                try:
                    incluster_ns = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read().strip()
                    cluster_name = f"in-cluster-{incluster_ns}"
                except Exception:
                    cluster_name = ""

            version_str = getattr(version, 'git_version', '')
            platform_str = getattr(version, 'platform', '')
            self._cluster_info = {
                "version": version_str,
                "platform": platform_str,
                "name": cluster_name,
            }

            nodes = self._core.list_node().items
            self._cluster_info["node_count"] = len(nodes)

            self._connected = True
            logger.info(f"Kubernetes connected: {version_str} cluster={cluster_name}")
            return True
        except Exception as e:
            self._connected = False
            logger.info("Kubernetes connection failed: %s", e)
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    def health_check(self) -> Dict[str, Any]:
        if not self._connected or not self._core:
            self.connect()

        if not self._connected or not self._core:
            if not self._kubeconfig_available():
                base = make_service_status(False, "Kubernetes", is_local_service=True)
                base["detail"] = "Kubernetes is not configured. Configure kubeconfig or run in a cluster."
                base.update({
                    "connected": False,
                    "cluster_name": "",
                    "server_version": "",
                    "node_count": 0,
                    "namespace_count": 0,
                    "deployment_count": 0,
                    "pod_count": 0,
                })
                return base
            base = make_service_status(False, "Kubernetes", is_local_service=is_cloud())
            base.update({
                "connected": False,
                "cluster_name": "",
                "server_version": "",
                "node_count": 0,
                "namespace_count": 0,
                "deployment_count": 0,
                "pod_count": 0,
            })
            return base

        try:
            version = client.VersionApi().get_code()
            nodes = self._core.list_node().items
            namespaces = self._core.list_namespace().items
            pods = self._core.list_pod_for_all_namespaces().items
            deployments = []
            try:
                deployments = self._apps.list_deployment_for_all_namespaces().items
            except Exception as e:
                logger.debug("Failed to list deployments for health check: %s", e)

            server_version = getattr(version, 'git_version', '')
            base = make_service_status(True, "Kubernetes")
            base["detail"] = "Kubernetes cluster is connected and operational."
            base.update({
                "connected": True,
                "cluster_name": self._cluster_info.get("name", ""),
                "server_version": server_version,
                "node_count": len(nodes),
                "namespace_count": len(namespaces),
                "deployment_count": len(deployments),
                "pod_count": len(pods),
            })
            return base
        except Exception as e:
            error_str = str(e)
            self._connected = False
            error_lower = error_str.lower()
            if "refused" in error_lower or "connection refused" in error_lower:
                if is_cloud():
                    base = make_service_status(False, "Kubernetes", is_local_service=True, error=error_str)
                    base["detail"] = "Kubernetes cluster is running in the local development environment. Running the backend locally enables full cluster monitoring."
                else:
                    base = make_service_status(False, "Kubernetes", error=error_str)
            elif "timeout" in error_lower or "timed out" in error_lower:
                base = make_service_status(False, "Kubernetes", error=error_str)
            elif "401" in error_str or "unauthorized" in error_lower or "authentication" in error_lower or "forbidden" in error_lower:
                base = make_service_status(False, "Kubernetes", error=error_str)
            else:
                base = make_service_status(False, "Kubernetes", error=error_str)
            base.update({
                "connected": False,
                "error": error_str,
                "cluster_name": "",
                "server_version": "",
                "node_count": 0,
                "namespace_count": 0,
                "deployment_count": 0,
                "pod_count": 0,
            })
            return base

    @staticmethod
    def _kubeconfig_available() -> bool:
        try:
            config.load_kube_config()
            return True
        except Exception:
            try:
                config.load_incluster_config()
                return True
            except Exception:
                return False

    def list_pods(
        self, namespace: str = "", label_selector: str = "", field_selector: str = ""
    ) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            if namespace:
                pods = self._core.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector,
                    field_selector=field_selector,
                )
            else:
                pods = self._core.list_pod_for_all_namespaces(
                    label_selector=label_selector,
                    field_selector=field_selector,
                )
            return [self._pod_to_dict(p) for p in pods.items]
        except ApiException as e:
            logger.error(f"Failed to list pods: {e}")
            return []

    def get_pod(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        if not self._core:
            return None
        try:
            pod = self._core.read_namespaced_pod(name=name, namespace=namespace)
            return self._pod_to_dict(pod)
        except ApiException as e:
            if e.status == 404:
                return None
            logger.warning(f"Failed to get pod {namespace}/{name}: {e}")
            return None

    def get_pod_logs(
        self,
        name: str,
        namespace: str = "default",
        container: str = "",
        tail: int = 100,
        previous: bool = False,
    ) -> Dict[str, Any]:
        if not self._core:
            return {"logs": "", "error": "Kubernetes not connected"}
        try:
            logs = self._core.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail,
                previous=previous,
                timestamps=True,
            )
            max_chars = 50000
            if len(logs) > max_chars:
                logs = logs[-max_chars:]
            return {"logs": logs, "truncated": len(logs) >= max_chars}
        except ApiException as e:
            return {"logs": "", "error": str(e)}

    def list_deployments(
        self, namespace: str = "", label_selector: str = ""
    ) -> List[Dict[str, Any]]:
        if not self._apps:
            return []
        try:
            if namespace:
                deps = self._apps.list_namespaced_deployment(
                    namespace=namespace, label_selector=label_selector
                )
            else:
                deps = self._apps.list_deployment_for_all_namespaces(
                    label_selector=label_selector
                )
            return [self._deployment_to_dict(d) for d in deps.items]
        except ApiException as e:
            logger.error(f"Failed to list deployments: {e}")
            return []

    def get_deployment(
        self, name: str, namespace: str = "default"
    ) -> Optional[Dict[str, Any]]:
        if not self._apps:
            return None
        try:
            dep = self._apps.read_namespaced_deployment(name=name, namespace=namespace)
            return self._deployment_to_dict(dep)
        except ApiException as e:
            if e.status == 404:
                return None
            logger.warning(f"Failed to get deployment {namespace}/{name}: {e}")
            return None

    def list_services(
        self, namespace: str = ""
    ) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            if namespace:
                svcs = self._core.list_namespaced_service(namespace=namespace)
            else:
                svcs = self._core.list_service_for_all_namespaces()
            return [
                {
                    "name": s.metadata.name,
                    "namespace": s.metadata.namespace,
                    "type": s.spec.type if s.spec else "",
                    "cluster_ip": s.spec.cluster_ip if s.spec else "",
                    "ports": [
                        {"port": p.port, "target_port": p.target_port, "protocol": p.protocol}
                        for p in (s.spec.ports or [])
                    ],
                }
                for s in svcs.items
            ]
        except ApiException as e:
            logger.error(f"Failed to list services: {e}")
            return []

    def list_ingresses(
        self, namespace: str = ""
    ) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            networking = client.NetworkingV1Api()
            if namespace:
                items = networking.list_namespaced_ingress(namespace=namespace).items
            else:
                items = networking.list_ingress_for_all_namespaces().items
            return [
                {
                    "name": i.metadata.name,
                    "namespace": i.metadata.namespace,
                    "rules": [
                        {"host": r.host, "http": {"paths": [p.path for p in (r.http.paths or [])]}}
                        for r in (i.spec.rules or [])
                    ],
                }
                for i in items
            ]
        except Exception as e:
            logger.error(f"Failed to list ingresses: {e}")
            return []

    def list_nodes(self) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            nodes = self._core.list_node().items
            return [
                {
                    "name": n.metadata.name,
                    "status": self._node_status(n),
                    "roles": self._node_roles(n),
                    "cpu_capacity": n.status.capacity.get("cpu", ""),
                    "memory_capacity": n.status.capacity.get("memory", ""),
                    "pod_capacity": n.status.capacity.get("pods", ""),
                    "cpu_allocatable": n.status.allocatable.get("cpu", ""),
                    "memory_allocatable": n.status.allocatable.get("memory", ""),
                    "kernel_version": n.status.node_info.kernel_version if n.status.node_info else "",
                    "os_image": n.status.node_info.os_image if n.status.node_info else "",
                    "container_runtime": n.status.node_info.container_runtime_version if n.status.node_info else "",
                    "labels": n.metadata.labels or {},
                    "annotations": n.metadata.annotations or {},
                    "conditions": [
                        {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
                        for c in (n.status.conditions or [])
                    ],
                }
                for n in nodes
            ]
        except ApiException as e:
            logger.error(f"Failed to list nodes: {e}")
            return []

    def list_events(
        self, namespace: str = "", field_selector: str = ""
    ) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            if namespace:
                events = self._core.list_namespaced_event(
                    namespace=namespace, field_selector=field_selector
                )
            else:
                events = self._core.list_event_for_all_namespaces(
                    field_selector=field_selector
                )
            return [
                {
                    "name": e.metadata.name,
                    "namespace": e.metadata.namespace,
                    "type": e.type,
                    "reason": e.reason,
                    "message": e.message,
                    "source": e.source.component if e.source else "",
                    "first_timestamp": to_iso(e.first_timestamp) or "",
                    "last_timestamp": to_iso(e.last_timestamp) or "",
                    "count": e.count,
                    "involved_object": {
                        "kind": e.involved_object.kind,
                        "name": e.involved_object.name,
                        "namespace": e.involved_object.namespace,
                    } if e.involved_object else {},
                }
                for e in events.items
            ]
        except ApiException as e:
            logger.error(f"Failed to list events: {e}")
            return []

    def get_cluster_metrics(self) -> Dict[str, Any]:
        pods = self.list_pods()
        nodes = self.list_nodes()
        deployments = self.list_deployments()

        total_pods = len(pods)
        running_pods = sum(1 for p in pods if p.get("phase") == "Running")
        pending_pods = sum(1 for p in pods if p.get("phase") == "Pending")
        failed_pods = sum(1 for p in pods if p.get("phase") == "Failed")
        crash_loop_pods = sum(
            1 for p in pods
            if any(
                cs.get("state_reason") == "CrashLoopBackOff"
                for cs in p.get("container_statuses", [])
            )
        )
        image_pull_backoff_pods = sum(
            1 for p in pods
            if any(
                cs.get("state_reason") == "ImagePullBackOff" or cs.get("state_reason") == "ErrImagePull"
                for cs in p.get("container_statuses", [])
            )
        )
        oom_pods = sum(
            1 for p in pods
            if any(
                cs.get("last_state_reason") == "OOMKilled"
                for cs in p.get("container_statuses", [])
            )
        )

        unavailable_deployments = sum(
            1 for d in deployments
            if d.get("unavailable_replicas", 0) > 0
        )

        unhealthy_nodes = sum(
            1 for n in nodes
            if n.get("status") != "Ready"
        )

        return {
            "total_pods": total_pods,
            "running_pods": running_pods,
            "pending_pods": pending_pods,
            "failed_pods": failed_pods,
            "crash_loop_back_off_pods": crash_loop_pods,
            "image_pull_back_off_pods": image_pull_backoff_pods,
            "oom_killed_pods": oom_pods,
            "total_nodes": len(nodes),
            "unhealthy_nodes": unhealthy_nodes,
            "total_deployments": len(deployments),
            "unavailable_deployments": unavailable_deployments,
        }

    def patch_deployment(self, name: str, namespace: str, body: dict) -> Dict[str, Any]:
        if not self._apps:
            return {"error": "Kubernetes not connected"}
        try:
            resp = self._apps.patch_namespaced_deployment(
                name=name, namespace=namespace, body=body
            )
            return {"success": True, "name": name, "namespace": namespace}
        except ApiException as e:
            logger.error(f"Failed to patch deployment {namespace}/{name}: {e}")
            return {"error": str(e), "success": False}

    def get_rollout_status(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        if not self._apps:
            return {"error": "Kubernetes not connected", "status": "unknown"}
        try:
            dep = self._apps.read_namespaced_deployment(name=name, namespace=namespace)
            status = dep.status
            spec = dep.spec
            conditions = []
            if status.conditions:
                for c in status.conditions:
                    conditions.append({
                        "type": c.type,
                        "status": c.status,
                        "reason": c.reason or "",
                        "message": c.message or "",
                        "last_transition_time": to_iso(c.last_transition_time) or "",
                    })
            available = status.available_replicas or 0
            desired = spec.replicas or 0
            updated = status.updated_replicas or 0
            ready = status.ready_replicas or 0

            if desired == 0:
                rollout_status = "paused"
            elif updated == desired and available == desired:
                rollout_status = "complete"
            elif updated < desired:
                rollout_status = "progressing"
            elif available < updated:
                rollout_status = "available"
            else:
                rollout_status = "unknown"

            return {
                "deployment": name,
                "namespace": namespace,
                "desired_replicas": desired,
                "updated_replicas": updated,
                "ready_replicas": ready,
                "available_replicas": available,
                "unavailable_replicas": status.unavailable_replicas or 0,
                "observed_generation": status.observed_generation or 0,
                "conditions": conditions,
                "status": rollout_status,
            }
        except ApiException as e:
            if e.status == 404:
                return {"error": "Deployment not found", "status": "not_found"}
            logger.error(f"Failed to get rollout status for {namespace}/{name}: {e}")
            return {"error": str(e), "status": "error"}
        except Exception as e:
            logger.error(f"Failed to get rollout status for {namespace}/{name}: {e}")
            return {"error": str(e), "status": "error"}

    def get_cluster_health(self) -> Dict[str, Any]:
        if not self._connected or not self._core:
            return {
                "connected": False,
                "nodes_total": 0,
                "nodes_ready": 0,
                "pods_running": 0,
                "pods_failed": 0,
            }
        try:
            nodes = self.list_nodes()
            pods = self.list_pods()

            nodes_total = len(nodes)
            nodes_ready = sum(1 for n in nodes if n.get("status") == "Ready")
            pods_running = sum(1 for p in pods if p.get("phase") == "Running")
            pods_failed = sum(1 for p in pods if p.get("phase") == "Failed")

            return {
                "connected": True,
                "nodes_total": nodes_total,
                "nodes_ready": nodes_ready,
                "pods_running": pods_running,
                "pods_failed": pods_failed,
            }
        except Exception as e:
            logger.error("Failed to get cluster health: %s", e)
            return {
                "connected": False,
                "error": str(e),
                "nodes_total": 0,
                "nodes_ready": 0,
                "pods_running": 0,
                "pods_failed": 0,
            }

    def list_namespaces(self) -> List[Dict[str, Any]]:
        if not self._core:
            return []
        try:
            nss = self._core.list_namespace().items
            return [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase if ns.status else "",
                    "labels": ns.metadata.labels or {},
                    "creation_timestamp": to_iso(ns.metadata.creation_timestamp) or "",
                }
                for ns in nss
            ]
        except ApiException as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []

    def find_pods_by_label(self, label_selector: str) -> List[Dict[str, Any]]:
        return self.list_pods(label_selector=label_selector)

    def find_pods_by_deployment(self, deployment_name: str, namespace: str = "default") -> List[Dict[str, Any]]:
        dep = self.get_deployment(name=deployment_name, namespace=namespace)
        if dep:
            selector = dep.get("selector", {})
            if selector:
                label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
                return self.list_pods(namespace=namespace, label_selector=label_selector)
        return self.list_pods(
            namespace=namespace,
            label_selector=f"app={deployment_name}",
        )

    def watch_events(self, callback):
        self._event_callback = callback
        if not self._watching:
            self._watching = True
            self._watcher = threading.Thread(target=self._watch_loop, daemon=True)
            self._watcher.start()
            logger.info("Kubernetes event watcher started")

    def _watch_loop(self):
        while self._watching:
            try:
                if not self._core:
                    logger.info("Kubernetes client not available, reconnecting...")
                    self.connect()
                    if not self._core:
                        time.sleep(5)
                        continue
                w = watch.Watch()
                for event in w.stream(
                    self._core.list_event_for_all_namespaces,
                    timeout_seconds=60,
                ):
                    if not self._watching:
                        break
                    try:
                        self._process_watch_event(event)
                    except Exception as e:
                        logger.debug(f"K8s event processing error: {e}")
            except Exception as e:
                logger.warning(f"Kubernetes watch error: {e}")
                self._connected = False
                self._core = None
                time.sleep(5)

    def _process_watch_event(self, event):
        if not self._event_callback:
            return
        obj = event.get("object", {})
        if not obj:
            return
        reason = obj.reason or ""
        message = obj.message or ""
        involved = obj.involved_object or {}
        kind = involved.kind or ""
        name = involved.name or ""
        namespace = involved.namespace or ""
        event_type = obj.type or ""

        data = {
            "reason": reason,
            "message": message,
            "kind": kind,
            "name": name,
            "namespace": namespace,
            "type": event_type,
        }

        if reason == "CrashLoopBackOff":
            self._event_callback("crash_loop_back_off", data)
        elif reason == "ImagePullBackOff" or reason == "ErrImagePull":
            self._event_callback("image_pull_back_off", data)
        elif reason == "FailedScheduling":
            self._event_callback("failed_scheduling", data)
        elif reason == "NodeNotReady":
            self._event_callback("node_not_ready", data)
        elif reason == "OOMKilling" or reason == "OOMKilled":
            self._event_callback("oom_killed", data)
        elif reason == "BackOff":
            if "restart" in message.lower():
                self._event_callback("pod_restarting", data)
        elif reason == "Unhealthy":
            self._event_callback("pod_unhealthy", data)

    def stop_watcher(self):
        self._watching = False
        if self._watcher and self._watcher.is_alive():
            self._watcher.join(timeout=3)

    @staticmethod
    def _pod_to_dict(pod) -> Dict[str, Any]:
        status = pod.status
        metadata = pod.metadata
        spec = pod.spec

        container_statuses = []
        if status.container_statuses:
            for cs in status.container_statuses:
                state = cs.state
                state_reason = ""
                state_detail = {}
                if state.running:
                    state_reason = "Running"
                    state_detail = {"started_at": to_iso(state.running.started_at) or ""}
                elif state.waiting:
                    state_reason = state.waiting.reason or "Waiting"
                    state_detail = {"message": state.waiting.message or ""}
                elif state.terminated:
                    state_reason = state.terminated.reason or "Terminated"
                    state_detail = {
                        "exit_code": state.terminated.exit_code,
                        "reason": state.terminated.reason or "",
                        "message": state.terminated.message or "",
                        "started_at": to_iso(state.terminated.started_at) or "",
                        "finished_at": to_iso(state.terminated.finished_at) or "",
                    }

                container_statuses.append({
                    "name": cs.name,
                    "ready": cs.ready,
                    "restart_count": cs.restart_count,
                    "image": cs.image,
                    "image_id": cs.image_id or "",
                    "state": state_reason,
                    "state_detail": state_detail,
                    "last_state_reason": cs.last_state.terminated.reason if cs.last_state and cs.last_state.terminated else "",
                    "started": cs.started if hasattr(cs, 'started') else False,
                })

        conditions = []
        if status.conditions:
            for c in status.conditions:
                conditions.append({
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason or "",
                    "message": c.message or "",
                    "last_transition_time": to_iso(c.last_transition_time) or "",
                })

        container_images = [c.image for c in (spec.containers or [])]

        node_name = spec.node_name or ""
        host_ip = status.host_ip or ""
        pod_ip = status.pod_ip or ""

        start_time = ""
        if status.start_time:
            start_time = to_iso(status.start_time)

        return {
            "name": metadata.name,
            "namespace": metadata.namespace,
            "phase": status.phase or "",
            "status": status.phase or "",
            "node": node_name,
            "host_ip": host_ip,
            "pod_ip": pod_ip,
            "restart_count": sum(cs.restart_count for cs in (status.container_statuses or [])),
            "container_count": len(spec.containers or []),
            "container_images": container_images,
            "container_statuses": container_statuses,
            "conditions": conditions,
            "start_time": start_time,
            "labels": metadata.labels or {},
            "annotations": metadata.annotations or {},
            "service_account": spec.service_account_name or "",
        }

    @staticmethod
    def _deployment_to_dict(dep) -> Dict[str, Any]:
        metadata = dep.metadata
        spec = dep.spec
        status = dep.status
        return {
            "name": metadata.name,
            "namespace": metadata.namespace,
            "replicas": spec.replicas if spec else 0,
            "ready_replicas": status.ready_replicas if status else 0,
            "available_replicas": status.available_replicas if status else 0,
            "unavailable_replicas": (status.unavailable_replicas or 0) if status else 0,
            "updated_replicas": status.updated_replicas if status else 0,
            "observed_generation": status.observed_generation if status else 0,
            "strategy": spec.strategy.type if spec and spec.strategy else "",
            "selector": spec.selector.match_labels if spec and spec.selector else {},
            "labels": metadata.labels or {},
            "annotations": metadata.annotations or {},
            "creation_timestamp": to_iso(metadata.creation_timestamp) or "",
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": [{"container_port": p.container_port, "protocol": p.protocol} for p in (c.ports or [])],
                    "resources": {
                        "limits": c.resources.limits if c.resources and c.resources.limits else {},
                        "requests": c.resources.requests if c.resources and c.resources.requests else {},
                    } if c.resources else {},
                }
                for c in (spec.template.spec.containers if spec and spec.template and spec.template.spec else [])
            ],
            "conditions": [
                {
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason or "",
                    "message": c.message or "",
                }
                for c in (status.conditions or [])
            ] if status else [],
        }

    @staticmethod
    def _node_status(node) -> str:
        if not node.status or not node.status.conditions:
            return "Unknown"
        for c in node.status.conditions:
            if c.type == "Ready":
                return "Ready" if c.status == "True" else "NotReady"
        return "Unknown"

    @staticmethod
    def _node_roles(node) -> List[str]:
        roles = []
        labels = node.metadata.labels or {}
        for key in labels:
            if key.startswith("node-role.kubernetes.io/"):
                roles.append(key.split("/")[-1])
        return roles
