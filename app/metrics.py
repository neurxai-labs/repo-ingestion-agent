from prometheus_client import Counter, Histogram

REPOS_PROCESSED_TOTAL = Counter(
    "repos_processed_total", "Total number of repositories processed"
)
REPO_PROCESS_SECONDS = Histogram(
    "repo_process_seconds", "Time spent processing a repository"
)
