from abc import ABC, abstractmethod

class BaseGitHubAuth(ABC):
    @abstractmethod
    def get_auth_headers(self) -> dict:
        pass


class PATGitHubAuth(BaseGitHubAuth):
    def __init__(self, token: str):
        self.token = token

    def get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


class OAuthGitHubAuth(BaseGitHubAuth):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}
