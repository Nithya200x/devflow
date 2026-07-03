import logging
import os
import random
from models import Cluster
from services.deployment_service import DeploymentService

logger = logging.getLogger(__name__)


class ClusterService:
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")

    @staticmethod
    def get_all_with_metrics():
        is_deploying = DeploymentService.check_and_update()
        clusters = Cluster.query.all()

        if ClusterService.DEMO_MODE:
            logger.info("ClusterService in DEMO_MODE — returning simulated metrics")
            return [{
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "node_count": c.node_count,
                "cpu_percent": random.randint(85, 98) if is_deploying else random.randint(30, 65),
                "mem_percent": random.randint(80, 95) if is_deploying else random.randint(40, 75),
                "pod_count": random.randint(15, 60),
                "demo_mode": True,
            } for c in clusters]

        return [{
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "node_count": c.node_count,
            "demo_mode": False,
        } for c in clusters]

    @staticmethod
    def get_logs(cluster_id):
        if ClusterService.DEMO_MODE:
            logger.info("ClusterService in DEMO_MODE — returning simulated logs")
            is_deploying = DeploymentService.check_and_update()
            if is_deploying:
                logs = [
                    "[INFO] Triggered rolling update for deployment/devflow-app",
                    "[INFO] Pulling new image registry.local/devflow-app:latest",
                    "[INFO] Terminating old pod devflow-app-5d6f5c88b9-old",
                    "[WARN] High CPU utilization during container startup",
                    "[INFO] Running database migrations via init container",
                    "[INFO] Liveness probe success for new pod devflow-app-5d6f5c88b9-new",
                ]
            else:
                logs = [
                    "[INFO] Node worker-1 joined cluster",
                    "[INFO] Pod devflow-api-7d6f5c88b9-x2j9k is Running",
                    "[WARN] Memory threshold crossed on node worker-2",
                    "[INFO] HTTP GET /health returned 200 OK",
                    "[INFO] Garbage collection freed 120MB on heap",
                    "[ERROR] Failed to connect to Redis cache (retry 1/3)",
                    "[INFO] Received metric payload from prometheus-agent",
                ]
            return random.sample(logs, k=random.randint(2, 5))

        return ["ClusterService: real cluster log aggregation not yet implemented"]
