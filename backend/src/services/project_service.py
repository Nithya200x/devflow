from models import Project

class ProjectService:

    @staticmethod
    def get_all():
        return Project.query.all()
