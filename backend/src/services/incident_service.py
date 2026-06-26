from models import Incident
from extensions import db
import logging

logger = logging.getLogger(__name__)

class IncidentService:

    @staticmethod
    def get_all():
        return Incident.query.order_by(Incident.created_at.desc()).all()

    @staticmethod
    def create(title, severity):
        i = Incident(title=title, severity=severity)
        db.session.add(i)
        db.session.commit()
        logger.info(f"Incident created: title={title}, severity={severity}")
        return i

    @staticmethod
    def update(incident_id, status):
        i = Incident.query.get_or_404(incident_id)
        if status:
            i.status = status
        db.session.commit()
        logger.info(f"Incident {incident_id} updated: status={status}")
        return i
