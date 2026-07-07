import logging
from models import Cluster

logger = logging.getLogger(__name__)


class ClusterService:

    @staticmethod
    def get_all_with_metrics():
        clusters = Cluster.query.all()
        return [{
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "node_count": c.node_count,
        } for c in clusters]

    @staticmethod
    def get_logs(cluster_id):
        return {"message": "Cluster logs are available via the Kubernetes pod logs endpoint at /api/v1/kubernetes/pods/<namespace>/<name>/logs"}
