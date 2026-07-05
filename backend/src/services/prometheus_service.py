import logging
import os
import time
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class PrometheusServiceError(Exception):
    pass


class PrometheusService:
    def __init__(self):
        raw = os.getenv("PROMETHEUS_URL", "").rstrip("/")
        self._username = os.getenv("PROMETHEUS_USERNAME", "")
        self._password = os.getenv("PROMETHEUS_PASSWORD", "")
        self._token = os.getenv("PROMETHEUS_TOKEN", "")
        self._base_url = self._normalize_url(raw)
        self._connected = False
        self._version = ""
        self._session: Optional[requests.Session] = None
        self._connect_time = 0.0

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return url
        url = url.rstrip("/")
        if "grafana" in url and "/api/prom" not in url:
            url = url + "/api/prom"
        return url

    def _setup_session(self):
        if self._session is not None:
            return
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        if self._token:
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})
        elif self._username and self._password:
            self._session.auth = (self._username, self._password)
        elif "grafana" in self._base_url:
            logger.warning(
                "Grafana Cloud Prometheus URL configured but PROMETHEUS_USERNAME and "
                "PROMETHEUS_PASSWORD are not set — queries will be rejected"
            )

    def connect(self) -> bool:
        if not self._base_url:
            logger.warning("PROMETHEUS_URL not set")
            self._connected = False
            return False

        self._setup_session()

        try:
            resp = self._session.get(f"{self._base_url}/api/v1/status/buildinfo", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._version = data.get("data", {}).get("version", "")
                self._connected = True
                self._connect_time = time.time()
                logger.info(f"Prometheus connected: {self._base_url} v{self._version}")
                return True
            logger.info("Prometheus buildinfo returned %s, trying up query", resp.status_code)
        except requests.RequestException as e:
            logger.info("Prometheus buildinfo failed: %s, trying up query", e)

        try:
            resp = self._session.get(
                f"{self._base_url}/api/v1/query",
                params={"query": "up"},
                timeout=10,
            )
            if resp.status_code == 200:
                self._connected = True
                self._version = "unknown"
                self._connect_time = time.time()
                logger.info("Prometheus connected via up query")
                return True
        except requests.RequestException as e:
            logger.info("Prometheus connection failed: %s", e)

        self._connected = False
        return False

    @property
    def connected(self) -> bool:
        return self._connected

    def _ensure_connected(self):
        if not self._connected or not self._session:
            self.connect()

    def query(self, query: str) -> Dict[str, Any]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return {"status": "error", "error": "Prometheus not connected"}
        try:
            resp = self._session.get(
                f"{self._base_url}/api/v1/query",
                params={"query": query},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Prometheus query failed: {e}")
            return {"status": "error", "error": str(e)}

    def instant_query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return {"status": "error", "error": "Prometheus not connected"}
        try:
            params = {"query": query}
            if time:
                params["time"] = time
            resp = self._session.get(
                f"{self._base_url}/api/v1/query",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Prometheus instant query failed: {e}")
            return {"status": "error", "error": str(e)}

    def range_query(
        self, query: str, start: str, end: str, step: str = "15s"
    ) -> Dict[str, Any]:
        self._ensure_connected()
        if not self._connected or not self._session:
            return {"status": "error", "error": "Prometheus not connected"}
        try:
            resp = self._session.get(
                f"{self._base_url}/api/v1/query_range",
                params={"query": query, "start": start, "end": end, "step": step},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Prometheus range query failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_cpu_metrics(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["pod_cpu_usage"] = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod="{pod}"}}[5m])'
        elif namespace:
            queries["namespace_cpu_usage"] = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m]))'
        queries["cluster_cpu_usage"] = "sum(rate(container_cpu_usage_seconds_total[5m])) / sum(machine_cpu_cores) * 100"
        return self._batch_query(queries)

    def get_memory_metrics(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["pod_memory_usage"] = f'container_memory_working_set_bytes{{namespace="{namespace}",pod="{pod}"}}'
        elif namespace:
            queries["namespace_memory_usage"] = f'sum(container_memory_working_set_bytes{{namespace="{namespace}"}})'
        queries["cluster_memory_usage"] = "sum(container_memory_working_set_bytes) / sum(machine_memory_bytes) * 100"
        return self._batch_query(queries)

    def get_disk_metrics(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["pod_disk_read"] = f'rate(container_fs_reads_bytes_total{{namespace="{namespace}",pod="{pod}"}}[5m])'
            queries["pod_disk_write"] = f'rate(container_fs_writes_bytes_total{{namespace="{namespace}",pod="{pod}"}}[5m])'
        queries["cluster_disk_usage"] = "sum(container_fs_usage_bytes) / sum(container_fs_limit_bytes) * 100"
        return self._batch_query(queries)

    def get_network_metrics(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["pod_network_rx"] = f'rate(container_network_receive_bytes_total{{namespace="{namespace}",pod="{pod}"}}[5m])'
            queries["pod_network_tx"] = f'rate(container_network_transmit_bytes_total{{namespace="{namespace}",pod="{pod}"}}[5m])'
        return self._batch_query(queries)

    def get_node_metrics(self, node: str = "") -> Dict[str, Any]:
        queries = {}
        if node:
            queries["node_cpu"] = f'100 - avg(rate(node_cpu_seconds_total{{mode="idle",node="{node}"}}[5m])) * 100'
            queries["node_memory"] = f'(1 - node_memory_MemAvailable_bytes{{node="{node}"}} / node_memory_MemTotal_bytes{{node="{node}"}}) * 100'
        else:
            queries["node_count"] = "count(node_cpu_seconds_total{mode='idle'})"
        return self._batch_query(queries)

    def get_deployment_metrics(self, namespace: str = "", deployment: str = "") -> Dict[str, Any]:
        queries = {}
        if deployment and namespace:
            queries["deployment_replicas"] = f'kube_deployment_status_replicas{{namespace="{namespace}",deployment="{deployment}"}}'
            queries["deployment_available"] = f'kube_deployment_status_replicas_available{{namespace="{namespace}",deployment="{deployment}"}}'
        return self._batch_query(queries)

    def get_service_metrics(self, namespace: str = "", service: str = "") -> Dict[str, Any]:
        queries = {}
        if service and namespace:
            queries["service_up"] = f'up{{namespace="{namespace}",service="{service}"}}'
        if namespace:
            queries["namespace_services"] = f'count(up{{namespace="{namespace}"}})'
        return self._batch_query(queries)

    def get_error_rate(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["error_rate"] = f'sum(rate(http_requests_total{{namespace="{namespace}",pod="{pod}",status=~"5.."}}[5m])) / sum(rate(http_requests_total{{namespace="{namespace}",pod="{pod}"}}[5m])) * 100'
        return self._batch_query(queries)

    def get_request_rate(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["request_rate"] = f'sum(rate(http_requests_total{{namespace="{namespace}",pod="{pod}"}}[5m]))'
        return self._batch_query(queries)

    def get_latency(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        queries = {}
        if pod and namespace:
            queries["latency_p99"] = f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{namespace="{namespace}",pod="{pod}"}}[5m])) by (le))'
        return self._batch_query(queries)

    def get_pod_metrics(self, namespace: str = "", pod: str = "") -> Dict[str, Any]:
        return {
            "cpu": self.get_cpu_metrics(namespace, pod),
            "memory": self.get_memory_metrics(namespace, pod),
            "disk": self.get_disk_metrics(namespace, pod),
            "network": self.get_network_metrics(namespace, pod),
        }

    def get_container_metrics(self, container_id: str = "") -> Dict[str, Any]:
        queries = {}
        if container_id:
            queries["container_cpu"] = f'rate(container_cpu_usage_seconds_total{{id="/docker/{container_id}"}}[5m])'
            queries["container_memory"] = f'container_memory_working_set_bytes{{id="/docker/{container_id}"}}'
        return self._batch_query(queries)

    def _batch_query(self, queries: Dict[str, str]) -> Dict[str, Any]:
        results = {}
        for name, q in queries.items():
            results[name] = self.query(q)
        return results

    def health_check(self) -> Dict[str, Any]:
        if not self._base_url:
            return {"connected": False, "error": "PROMETHEUS_URL not configured", "version": "", "latency_ms": 0}

        if not self._connected:
            self.connect()

        if not self._session:
            self._setup_session()

        try:
            start = time.time()
            resp = self._session.get(
                f"{self._base_url}/api/v1/query",
                params={"query": "up"},
                timeout=5,
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                data = resp.json()
                result_count = len(data.get("data", {}).get("result", []))
                return {
                    "connected": True,
                    "has_metrics": result_count > 0,
                    "version": self._version or "unknown",
                    "latency_ms": round(elapsed, 2),
                    "error": None,
                }
            self._connected = False
            return {"connected": False, "version": "", "latency_ms": round(elapsed, 2), "error": f"HTTP {resp.status_code}"}
        except requests.RequestException as e:
            self._connected = False
            return {"connected": False, "version": "", "latency_ms": 0, "error": str(e)}

    def list_active_alerts(self) -> List[Dict[str, Any]]:
        result = self.query("ALERTS{alertstate='firing'}")
        alerts = []
        try:
            for series in (result.get("data", {}).get("result", [])):
                metric = series.get("metric", {})
                alerts.append({
                    "alertname": metric.get("alertname", ""),
                    "severity": metric.get("severity", ""),
                    "alertstate": metric.get("alertstate", ""),
                    "instance": metric.get("instance", ""),
                    "job": metric.get("job", ""),
                    "namespace": metric.get("namespace", ""),
                    "pod": metric.get("pod", ""),
                    "value": series.get("value", [None, None])[1],
                })
        except Exception as e:
            logger.debug(f"Failed to parse alerts: {e}")
        return alerts


prometheus_service = PrometheusService()
