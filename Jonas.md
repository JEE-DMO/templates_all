OK. Voilà une **recette CI/CD “propre”** pour déployer une appli Python (API FastAPI / worker / script) — je te donne 2 chemins simples :

* **A) Docker + Kubernetes (le plus “standard” en entreprise)**
* **B) Sans K8S : build + déploiement sur VM via SSH (rapide et efficace)**

---

## A) CI/CD Docker → Registry → Kubernetes

### 1) Dockerfile (exemple)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2) .dockerignore (important)

```
.venv
__pycache__
*.pyc
.git
tests
```

### 3) Manifests K8S (deployment + service)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels: { app: myapp }
  template:
    metadata:
      labels: { app: myapp }
    spec:
      containers:
        - name: myapp
          image: REGISTRY/myapp:__TAG__
          ports: [{ containerPort: 8000 }]
          env:
            - name: ENV
              value: "prod"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector: { app: myapp }
  ports:
    - port: 80
      targetPort: 8000
```

### 4) Pipeline GitLab CI (exemple complet)

> si tu es sur GitHub Actions, dis-moi et je te donne l’équivalent.

```yaml
stages: [lint, test, build, deploy]

variables:
  IMAGE: "$CI_REGISTRY_IMAGE/myapp"
  DOCKER_TLS_CERTDIR: ""

lint:
  image: python:3.12
  stage: lint
  script:
    - pip install ruff
    - ruff check .

test:
  image: python:3.12
  stage: test
  script:
    - pip install -r requirements.txt
    - pip install pytest
    - pytest -q

build:
  image: docker:27
  stage: build
  services: ["docker:27-dind"]
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
    - docker build -t "$IMAGE:$CI_COMMIT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHA"
    - docker tag "$IMAGE:$CI_COMMIT_SHA" "$IMAGE:latest"
    - docker push "$IMAGE:latest"
  only:
    - main

deploy:
  image: bitnami/kubectl:latest
  stage: deploy
  script:
    - kubectl config use-context "$KUBE_CONTEXT"
    - sed "s|REGISTRY/myapp:__TAG__|$IMAGE:$CI_COMMIT_SHA|g" k8s.yaml | kubectl apply -f -
    - kubectl rollout status deploy/myapp
  only:
    - main
```

**Secrets à configurer dans CI :**

* `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` (souvent déjà fournis GitLab)
* `KUBE_CONTEXT` + accès kubeconfig (ou token/cluster creds selon ton setup)

**Bonnes pratiques** :

* Tagger avec `CI_COMMIT_SHA` (immutabilité)
* Ajouter un step “security scan” (trivy) si nécessaire
* Faire un `rollout status` pour vérifier le déploiement

---

## B) CI/CD sur VM (sans K8S) via SSH + systemd

### 1) Pipeline : build + rsync + restart service

```yaml
stages: [test, deploy]

test:
  image: python:3.12
  stage: test
  script:
    - pip install -r requirements.txt
    - pip install pytest
    - pytest -q

deploy:
  image: alpine:latest
  stage: deploy
  before_script:
    - apk add --no-cache openssh rsync
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H "$VM_HOST" >> ~/.ssh/known_hosts
  script:
    - rsync -az --delete ./ "$VM_USER@$VM_HOST:/opt/myapp/"
    - ssh "$VM_USER@$VM_HOST" "cd /opt/myapp && /opt/myapp/venv/bin/pip install -r requirements.txt"
    - ssh "$VM_USER@$VM_HOST" "sudo systemctl restart myapp"
  only:
    - main
```

### 2) systemd service sur la VM

```ini
[Unit]
Description=My Python App
After=network.target

[Service]
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
User=appuser
Environment=ENV=prod

[Install]
WantedBy=multi-user.target
```

---

## Ce que j’ai besoin de savoir (pour te donner EXACTEMENT le bon template)

Réponds juste par **A/B + 3 infos** (sans blabla) :

1. Tu es sur **GitLab CI** ou **GitHub Actions** ?
2. Cible : **Kubernetes** (oui/non) ?
3. Type d’app : **FastAPI / Flask / script / Airflow DAG / autre** ?

Et je te fournis le pipeline final “copier-coller” adapté (avec les variables/secrets à créer).
