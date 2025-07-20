# repo-ingestion-agent

## Dockerization

### Build the Docker image

```bash
docker build -t neurxai-labs/repo-ingestion-agent .
```

### Run the Docker container

```bash
docker run -d -p 8001:8001 --env-file .env neurxai-labs/repo-ingestion-agent
```

### Test the service

To test the service, you can send a POST request to the `/register-repo` endpoint.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"repo_url": "<url>", "repo_id": "test"}' http://localhost:8001/register-repo
```

You can then check the logs of the container to see the output of the cloning, chunking, and publishing process.

```bash
docker logs <container_id>
```

## Load Testing with Locust

This directory contains a Locust load test for the repository processing service.

### Running the Load Test

1.  Install Locust:

    ```bash
    pip install locust
    ```

2.  Run the load test:

    ```bash
    locust -f loadtests/locustfile.py --host http://localhost:8000
    ```

3.  Open a web browser and navigate to `http://localhost:8089` to start the load test.


## Monitoring

The service exposes Prometheus metrics on the `/metrics` endpoint on port `8001` by default. You can scrape this endpoint with a Prometheus server to monitor the service.