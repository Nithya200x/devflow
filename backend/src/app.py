import os
import socket
from uuid import getnode as get_mac
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db, User, Project, Cluster, Incident, Deployment
from api import api_bp

APP_NAME = os.getenv("APP_NAME", "DevFlow SaaS")
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")

# Database goes in the "database" folder at the root of the project
basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
database_dir = os.path.join(basedir, 'database')
# Ensure database directory exists
os.makedirs(database_dir, exist_ok=True)
db_path = os.path.join(database_dir, 'app.db')

def create_app():
    app = Flask(__name__)
    
    # Configure Database and JWT
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'devflow-super-secret-key-change-in-prod'  # Change this in production
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Seed mock data if database exists and is empty
    # In a real app with migrations, seeding usually happens in a separate script or migration step.
    # We will keep this for convenience but only run if users table exists and is empty.
    with app.app_context():
        try:
            seed_data()
        except Exception as e:
            # If the tables are not created yet (e.g. before `flask db upgrade`), it will throw an exception
            pass

    @app.route("/health")
    def health():
        return jsonify(
            app=APP_NAME,
            status="up",
            version=APP_VERSION,
        )

    return app

def seed_data():
    if User.query.first() is None:
        # Create mock users
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        dev = User(username="developer", role="developer")
        dev.set_password("dev123")
        db.session.add_all([admin, dev])
        
        # Create mock projects
        p1 = Project(name="Payment Gateway", repository_url="https://github.com/nithya200x/payment-gw", description="Core payment processing service")
        p2 = Project(name="Auth Service", repository_url="https://github.com/nithya200x/auth-service", description="OAuth2 authentication service")
        db.session.add_all([p1, p2])
        db.session.commit() # commit to get project IDs
        
        # Create mock deployments
        d1 = Deployment(project_id=p1.id, environment="prod", status="success", deployed_by="admin")
        d2 = Deployment(project_id=p2.id, environment="staging", status="failed", deployed_by="developer")
        d3 = Deployment(project_id=p1.id, environment="dev", status="running", deployed_by="admin")
        db.session.add_all([d1, d2, d3])
        
        # Create mock clusters
        c1 = Cluster(name="prod-cluster-east", status="active", node_count=5)
        c2 = Cluster(name="dev-cluster", status="active", node_count=2)
        db.session.add_all([c1, c2])
        
        # Create mock incidents
        i1 = Incident(title="High API Latency", status="investigating", severity="high")
        i2 = Incident(title="Database Backup Failed", status="open", severity="critical")
        db.session.add_all([i1, i2])
        
        db.session.commit()
        print("Mock data seeded successfully!")

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
