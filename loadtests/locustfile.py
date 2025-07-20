import random
from locust import HttpUser, task, between

class RepoUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def register_repo(self):
        repo_id = f"test-repo-{random.randint(1, 1000)}"
        self.client.post("/register-repo", json={"repo_url": f"https://github.com/test/{repo_id}", "repo_id": repo_id})
