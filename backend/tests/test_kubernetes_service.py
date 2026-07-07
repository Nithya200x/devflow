import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from services.kubernetes_service import KubernetesService


def make_mock_node(name, ready=True):
    cond = MagicMock()
    cond.type = "Ready"
    cond.status = "True" if ready else "False"
    cond.reason = ""
    cond.message = ""
    node = MagicMock()
    node.metadata.name = name
    node.metadata.labels = {"kubernetes.io/hostname": name}
    node.metadata.annotations = {}
    node.status.conditions = [cond]
    node.status.capacity = {"cpu": "4", "memory": "16Gi", "pods": "110"}
    node.status.allocatable = {"cpu": "3", "memory": "14Gi", "pods": "110"}
    node.status.node_info.kernel_version = "6.2.0"
    node.status.node_info.os_image = "Ubuntu 22.04"
    node.status.node_info.container_runtime_version = "containerd://1.7.0"
    return node


def make_mock_pod(name, namespace, phase="Running", restart_count=0, image="nginx:latest"):
    cs = MagicMock()
    cs.name = "container-0"
    cs.ready = True
    cs.restart_count = restart_count
    cs.image = image
    cs.image_id = f"docker-pullable://{image}"
    cs.started = True
    cs.state.running.started_at = None
    cs.state.waiting = None
    cs.state.terminated = None
    cs.last_state.terminated = None

    status = MagicMock()
    status.phase = phase
    status.container_statuses = [cs]
    status.conditions = []
    status.host_ip = "10.0.0.1"
    status.pod_ip = "10.1.0.1"
    status.start_time = None

    container = MagicMock()
    container.name = "container-0"
    container.image = image

    spec = MagicMock()
    spec.containers = [container]
    spec.node_name = "node-1"
    spec.service_account_name = "default"

    metadata = MagicMock()
    metadata.name = name
    metadata.namespace = namespace
    metadata.labels = {"app": name.split("-")[0]}
    metadata.annotations = {}
    metadata.creation_timestamp = None

    pod = MagicMock()
    pod.metadata = metadata
    pod.status = status
    pod.spec = spec
    return pod


def make_mock_deployment(name, namespace, replicas=1, ready=1, available=1):
    status = MagicMock()
    status.ready_replicas = ready
    status.available_replicas = available
    status.unavailable_replicas = replicas - ready
    status.updated_replicas = ready
    status.observed_generation = 1
    status.conditions = []

    strategy = MagicMock()
    strategy.type = "RollingUpdate"

    selector = MagicMock()
    selector.match_labels = {"app": name}

    port = MagicMock()
    port.container_port = 5000
    port.protocol = "TCP"

    container = MagicMock()
    container.name = name
    container.image = f"{name}:latest"
    container.ports = [port]
    container.resources = MagicMock()
    container.resources.limits = {}
    container.resources.requests = {}

    template_spec = MagicMock()
    template_spec.containers = [container]

    template = MagicMock()
    template.spec = template_spec

    spec = MagicMock()
    spec.replicas = replicas
    spec.strategy = strategy
    spec.selector = selector
    spec.template = template

    metadata = MagicMock()
    metadata.name = name
    metadata.namespace = namespace
    metadata.labels = {"app": name}
    metadata.annotations = {}
    metadata.creation_timestamp = None

    dep = MagicMock()
    dep.metadata = metadata
    dep.spec = spec
    dep.status = status
    return dep


def make_mock_service(name, namespace, svc_type="ClusterIP", cluster_ip="10.0.0.1", ports=None):
    if ports is None:
        p = MagicMock()
        p.port = 80
        p.target_port = 80
        p.protocol = "TCP"
        ports = [p]

    spec = MagicMock()
    spec.type = svc_type
    spec.cluster_ip = cluster_ip
    spec.ports = ports

    metadata = MagicMock()
    metadata.name = name
    metadata.namespace = namespace

    svc = MagicMock()
    svc.metadata = metadata
    svc.spec = spec
    return svc


class TestKubernetesService:
    def test_get_cluster_health_unavailable(self):
        svc = KubernetesService()
        health = svc.get_cluster_health()
        assert health["connected"] is False
        assert health["nodes_total"] == 0
        assert health["nodes_ready"] == 0
        assert health["pods_running"] == 0
        assert health["pods_failed"] == 0

    @patch("services.kubernetes_service.client")
    def test_get_cluster_health_success(self, mock_client):
        mock_core = MagicMock()
        mock_core.list_node.return_value.items = [
            make_mock_node("node-1", ready=True),
            make_mock_node("node-2", ready=True),
        ]
        mock_core.list_pod_for_all_namespaces.return_value.items = [
            make_mock_pod("pod-1", "default", phase="Running"),
            make_mock_pod("pod-2", "default", phase="Running"),
            make_mock_pod("pod-3", "default", phase="Failed"),
        ]
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        health = svc.get_cluster_health()
        assert health["connected"] is True
        assert health["nodes_total"] == 2
        assert health["nodes_ready"] == 2
        assert health["pods_running"] == 2
        assert health["pods_failed"] == 1

    @patch("services.kubernetes_service.client")
    def test_list_pods_all_namespaces(self, mock_client):
        mock_core = MagicMock()
        mock_core.list_pod_for_all_namespaces.return_value.items = [
            make_mock_pod("backend-abc", "devflow", phase="Running", restart_count=2, image="devflow-backend:latest"),
            make_mock_pod("frontend-def", "devflow", phase="Running", restart_count=0, image="devflow-frontend:latest"),
        ]
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        pods = svc.list_pods()
        assert len(pods) == 2
        assert pods[0]["name"] == "backend-abc"
        assert pods[0]["namespace"] == "devflow"
        assert pods[0]["phase"] == "Running"
        assert pods[0]["restart_count"] == 2
        assert pods[1]["name"] == "frontend-def"
        assert pods[1]["restart_count"] == 0

    @patch("services.kubernetes_service.client")
    def test_list_pods_namespaced(self, mock_client):
        mock_core = MagicMock()
        mock_core.list_namespaced_pod.return_value.items = [
            make_mock_pod("prom-xyz", "devflow", phase="Running"),
        ]
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        pods = svc.list_pods(namespace="devflow")
        assert len(pods) == 1
        assert pods[0]["namespace"] == "devflow"

    @patch("services.kubernetes_service.client")
    def test_list_pods_api_error(self, mock_client):
        from kubernetes.client.rest import ApiException

        mock_core = MagicMock()
        mock_core.list_pod_for_all_namespaces.side_effect = ApiException(status=403, reason="Forbidden")
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        pods = svc.list_pods()
        assert pods == []

    @patch("services.kubernetes_service.client")
    def test_list_deployments(self, mock_client):
        mock_apps = MagicMock()
        mock_apps.list_deployment_for_all_namespaces.return_value.items = [
            make_mock_deployment("backend", "devflow", replicas=3, ready=3, available=3),
            make_mock_deployment("frontend", "devflow", replicas=2, ready=1, available=1),
        ]
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        deps = svc.list_deployments()
        assert len(deps) == 2
        assert deps[0]["name"] == "backend"
        assert deps[0]["ready_replicas"] == 3
        assert deps[0]["replicas"] == 3
        assert deps[0]["available_replicas"] == 3
        assert deps[1]["name"] == "frontend"
        assert deps[1]["ready_replicas"] == 1

    @patch("services.kubernetes_service.client")
    def test_list_deployments_namespaced(self, mock_client):
        mock_apps = MagicMock()
        mock_apps.list_namespaced_deployment.return_value.items = [
            make_mock_deployment("backend", "devflow", replicas=1, ready=1, available=1),
        ]
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        deps = svc.list_deployments(namespace="devflow")
        assert len(deps) == 1
        assert deps[0]["namespace"] == "devflow"

    @patch("services.kubernetes_service.client")
    def test_list_deployments_api_error(self, mock_client):
        from kubernetes.client.rest import ApiException

        mock_apps = MagicMock()
        mock_apps.list_deployment_for_all_namespaces.side_effect = ApiException(status=403, reason="Forbidden")
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        deps = svc.list_deployments()
        assert deps == []

    @patch("services.kubernetes_service.client")
    def test_list_services(self, mock_client):
        mock_core = MagicMock()
        port_80 = MagicMock()
        port_80.port = 80
        port_80.target_port = 80
        port_80.protocol = "TCP"
        port_5000 = MagicMock()
        port_5000.port = 5000
        port_5000.target_port = 5000
        port_5000.protocol = "TCP"

        mock_core.list_service_for_all_namespaces.return_value.items = [
            make_mock_service("frontend", "devflow", "ClusterIP", "10.0.0.2", ports=[port_80]),
            make_mock_service("backend", "devflow", "ClusterIP", "10.0.0.3", ports=[port_5000]),
        ]
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        services = svc.list_services()
        assert len(services) == 2
        assert services[0]["name"] == "frontend"
        assert services[0]["type"] == "ClusterIP"
        assert services[0]["cluster_ip"] == "10.0.0.2"
        assert services[0]["ports"][0]["port"] == 80
        assert services[1]["name"] == "backend"
        assert services[1]["ports"][0]["port"] == 5000

    @patch("services.kubernetes_service.client")
    def test_list_services_namespaced(self, mock_client):
        mock_core = MagicMock()
        port = MagicMock()
        port.port = 5432
        port.target_port = 5432
        port.protocol = "TCP"
        mock_core.list_namespaced_service.return_value.items = [
            make_mock_service("postgres", "devflow", "ClusterIP", "10.0.0.4", ports=[port]),
        ]
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        services = svc.list_services(namespace="devflow")
        assert len(services) == 1
        assert services[0]["name"] == "postgres"
        assert services[0]["ports"][0]["port"] == 5432

    @patch("services.kubernetes_service.client")
    def test_list_services_api_error(self, mock_client):
        from kubernetes.client.rest import ApiException

        mock_core = MagicMock()
        mock_core.list_service_for_all_namespaces.side_effect = ApiException(status=403, reason="Forbidden")
        mock_client.CoreV1Api.return_value = mock_core

        svc = KubernetesService()
        svc._core = mock_core
        svc._connected = True

        services = svc.list_services()
        assert services == []

    def test_cluster_health_reports_error_on_exception(self):
        svc = KubernetesService()
        svc._connected = True
        svc._core = MagicMock()
        svc._core.list_node.side_effect = Exception("API unavailable")

        health = svc.get_cluster_health()
        assert health["connected"] is False
        assert "API unavailable" in health.get("error", "")


class TestGetRolloutStatus:
    def test_returns_error_when_not_connected(self):
        svc = KubernetesService()
        result = svc.get_rollout_status("backend", "devflow")
        assert result["error"] == "Kubernetes not connected"
        assert result["status"] == "unknown"

    @patch("services.kubernetes_service.client")
    def test_returns_status_complete(self, mock_client):
        dep = make_mock_deployment("backend", "devflow", replicas=3, ready=3, available=3)
        dep.status.conditions = []
        dep.status.unavailable_replicas = 0
        dep.status.observed_generation = 2

        mock_apps = MagicMock()
        mock_apps.read_namespaced_deployment.return_value = dep
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        result = svc.get_rollout_status("backend", "devflow")
        assert result["deployment"] == "backend"
        assert result["namespace"] == "devflow"
        assert result["status"] == "complete"
        assert result["desired_replicas"] == 3
        assert result["available_replicas"] == 3
        assert result["ready_replicas"] == 3

    @patch("services.kubernetes_service.client")
    def test_returns_status_progressing(self, mock_client):
        dep = make_mock_deployment("backend", "devflow", replicas=3, ready=1, available=0)
        dep.status.updated_replicas = 1
        dep.status.unavailable_replicas = 2
        dep.status.observed_generation = 1

        mock_apps = MagicMock()
        mock_apps.read_namespaced_deployment.return_value = dep
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        result = svc.get_rollout_status("backend", "devflow")
        assert result["status"] == "progressing"

    @patch("services.kubernetes_service.client")
    def test_returns_404_when_not_found(self, mock_client):
        from kubernetes.client.rest import ApiException
        mock_apps = MagicMock()
        mock_apps.read_namespaced_deployment.side_effect = ApiException(status=404, reason="Not Found")
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        result = svc.get_rollout_status("nonexistent", "devflow")
        assert result["status"] == "not_found"

    @patch("services.kubernetes_service.client")
    def test_returns_conditions(self, mock_client):
        dep = make_mock_deployment("backend", "devflow", replicas=1, ready=1, available=1)
        c1 = MagicMock()
        c1.type = "Available"
        c1.status = "True"
        c1.reason = "MinimumReplicasAvailable"
        c1.message = "Deployment has minimum availability."
        c1.last_transition_time = None
        dep.status.conditions = [c1]

        mock_apps = MagicMock()
        mock_apps.read_namespaced_deployment.return_value = dep
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        result = svc.get_rollout_status("backend", "devflow")
        assert len(result["conditions"]) == 1
        assert result["conditions"][0]["type"] == "Available"
        assert result["conditions"][0]["reason"] == "MinimumReplicasAvailable"


class TestPatchDeployment:
    def test_returns_error_when_not_connected(self):
        svc = KubernetesService()
        result = svc.patch_deployment("backend", "devflow", {"spec": {"replicas": 3}})
        assert result["error"] == "Kubernetes not connected"

    @patch("services.kubernetes_service.client")
    def test_patches_successfully(self, mock_client):
        mock_apps = MagicMock()
        mock_apps.patch_namespaced_deployment.return_value = MagicMock()
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        body = {"spec": {"replicas": 5}}
        result = svc.patch_deployment("backend", "devflow", body)
        assert result["success"] is True
        assert result["name"] == "backend"
        mock_apps.patch_namespaced_deployment.assert_called_once_with(
            name="backend", namespace="devflow", body=body,
        )

    @patch("services.kubernetes_service.client")
    def test_returns_error_on_api_exception(self, mock_client):
        from kubernetes.client.rest import ApiException
        mock_apps = MagicMock()
        mock_apps.patch_namespaced_deployment.side_effect = ApiException(status=500, reason="Server Error")
        mock_client.AppsV1Api.return_value = mock_apps

        svc = KubernetesService()
        svc._apps = mock_apps
        svc._connected = True

        result = svc.patch_deployment("backend", "devflow", {})
        assert result["success"] is False
        assert "500" in result["error"]
