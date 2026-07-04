from models import ConnectedProject

class ConnectedProjectService:

    @staticmethod
    def get_by_user(username):
        return ConnectedProject.query.filter_by(connected_by=username).order_by(ConnectedProject.connected_at.desc()).all()

    @staticmethod
    def get_by_id(project_id):
        return ConnectedProject.query.get(project_id)

    @staticmethod
    def get_by_repo_id(repo_id, username):
        return ConnectedProject.query.filter_by(github_repo_id=repo_id, connected_by=username).first()
