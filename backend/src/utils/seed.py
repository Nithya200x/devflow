from models import User, Project, Cluster, Deployment, Incident
from extensions import db

def seed_data():
    if User.query.first() is None:
        admin = User(name="Admin", email="admin@devflow.local", username="admin", role="admin")
        admin.set_password("admin123")
        dev = User(name="Developer", email="dev@devflow.local", username="developer", role="developer")
        dev.set_password("dev123")
        db.session.add_all([admin, dev])

        p1 = Project(name="Payment Gateway", repository_url="https://github.com/nithya200x/payment-gw", description="Core payment processing service")
        p2 = Project(name="Auth Service", repository_url="https://github.com/nithya200x/auth-service", description="OAuth2 authentication service")
        db.session.add_all([p1, p2])
        db.session.commit()

        d1 = Deployment(project_id=p1.id, environment="prod", status="success", deployed_by="admin")
        d2 = Deployment(project_id=p2.id, environment="staging", status="failed", deployed_by="developer")
        d3 = Deployment(project_id=p1.id, environment="dev", status="running", deployed_by="admin")
        db.session.add_all([d1, d2, d3])

        c1 = Cluster(name="prod-cluster-east", status="active", node_count=5)
        c2 = Cluster(name="dev-cluster", status="active", node_count=2)
        db.session.add_all([c1, c2])

        i1 = Incident(title="High API Latency", status="investigating", severity="high")
        i2 = Incident(title="Database Backup Failed", status="open", severity="critical")
        db.session.add_all([i1, i2])

        db.session.commit()
        print("Mock data seeded successfully!")
