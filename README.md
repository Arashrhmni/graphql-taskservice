# GraphQL Task Service

A cloud-native microservice exposing a **GraphQL API** for task management.  
Built with **FastAPI + Strawberry**, containerised with Docker, and deployable to Kubernetes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.115 |
| GraphQL | Strawberry 0.243 |
| Server | Uvicorn (ASGI) |
| Tests | pytest + httpx |
| Container | Docker (multi-stage) |
| Orchestration | Kubernetes + Helm |
| CI | GitHub Actions |

---

## Project Structure

```
graphql-taskservice/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── graphql/
│   │   └── schema.py        # Strawberry types, queries, mutations
│   └── models/
│       └── task.py          # Domain model + in-memory store
├── tests/
│   ├── unit/
│   │   ├── test_task_model.py   # 18 unit tests — store logic
│   │   └── test_schema.py       # 12 unit tests — GraphQL resolvers
│   └── integration/
│       └── test_api.py          # 7 integration tests — HTTP round-trips
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   └── ingress.yaml
├── helm/graphql-taskservice/   # Helm chart
├── .github/workflows/ci.yml    # GitHub Actions CI
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml
└── requirements.txt
```

---

## Quick Start (Local)

### 1 — Run directly with Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000/graphql** — GraphiQL playground is live.

---

### 2 — Run with Docker

```bash
# Build and start
docker compose up api

# Or build manually
docker build -t graphql-taskservice:local .
docker run -p 8000:8000 graphql-taskservice:local
```

---

### 3 — Hot-reload dev server

```bash
docker compose --profile dev up api-dev
# Service available on http://localhost:8001/graphql
```

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Via Docker
docker compose --profile test up tests --abort-on-container-exit
```

---

## GraphQL API

### Queries

#### List tasks (with optional filters)
```graphql
query {
  tasks(status: "TODO", priority: "HIGH", tag: "devops") {
    id
    title
    description
    priority
    status
    tags
    createdAt
    updatedAt
  }
}
```

#### Get a single task
```graphql
query {
  task(id: "your-task-id") {
    id
    title
    status
  }
}
```

---

### Mutations

#### Create a task
```graphql
mutation {
  createTask(input: {
    title: "Write Kubernetes manifests"
    description: "Deployment, Service, HPA"
    priority: "HIGH"
    tags: ["devops", "k8s"]
  }) {
    id
    title
    status
  }
}
```

#### Update a task
```graphql
mutation {
  updateTask(input: {
    id: "your-task-id"
    status: "IN_PROGRESS"
    priority: "HIGH"
  }) {
    id
    status
  }
}
```

#### Delete a task
```graphql
mutation {
  deleteTask(id: "your-task-id") {
    success
    message
  }
}
```

---

### Enum values

**Priority:** `LOW` | `MEDIUM` | `HIGH`  
**Status:** `TODO` | `IN_PROGRESS` | `DONE`

---

## Kubernetes Deployment

### Plain manifests (minikube / kind)

```bash
# Load image into minikube
minikube image load graphql-taskservice:1.0.0

# Apply all manifests
kubectl apply -f k8s/

# Check rollout
kubectl rollout status deployment/graphql-taskservice

# Port-forward to test locally
kubectl port-forward svc/graphql-taskservice 8080:80
# -> http://localhost:8080/graphql
```

---

### Helm chart

```bash
# Install
helm install taskservice ./helm/graphql-taskservice

# With custom values
helm install taskservice ./helm/graphql-taskservice \
  --set image.repository=myregistry/graphql-taskservice \
  --set image.tag=1.0.0 \
  --set replicaCount=3 \
  --set ingress.enabled=true \
  --set ingress.host=api.example.com

# Upgrade
helm upgrade taskservice ./helm/graphql-taskservice

# Uninstall
helm uninstall taskservice
```

---

## CI/CD (GitHub Actions)

The `.github/workflows/ci.yml` pipeline:

1. **Runs tests** on Python 3.11 and 3.12 (matrix)
2. **Builds the Docker image** with BuildKit layer caching
3. **Smoke-tests the container** by hitting `/health`

Triggered on push to `main`/`develop` and all pull requests.

---

## Health Check

```
GET /health
→ {"status": "ok", "service": "graphql-taskservice"}
```

---

## Resume Bullet

> **Developed and containerised a GraphQL microservice** (FastAPI + Strawberry) with full CRUD operations, 40+ pytest unit and integration tests, a multi-stage Dockerfile, docker-compose local dev workflow, and Kubernetes deployment manifests (Deployment, Service, HPA) with a Helm chart for parameterised releases.
