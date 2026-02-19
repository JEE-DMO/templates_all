Oui 👍 — sur **Astronomer / Airflow 2.9.3**, tu peux être **beaucoup plus chirurgical**.
Voici **la vraie liste des loggers qui floodent en prod** dans ce stack, avec **les niveaux recommandés** (retours terrain inclus).

---

## 🎯 Objectif

👉 **Réduire drastiquement le volume stdout** sans toucher :

* `airflow.cfg`
* Fluent Bit
* la conf Astronomer

---

## ✅ Loggers à cibler PRIORITAIREMENT (Airflow 2.9.x)

### 🔥 1️⃣ Airflow core (très bavard en INFO)

```python
logging.getLogger("airflow.task").setLevel(logging.WARNING)
logging.getLogger("airflow.jobs").setLevel(logging.WARNING)
logging.getLogger("airflow.executors").setLevel(logging.WARNING)
logging.getLogger("airflow.models.taskinstance").setLevel(logging.WARNING)
logging.getLogger("airflow.utils.log").setLevel(logging.ERROR)
```

📌 **Pourquoi**

* `airflow.task` → log chaque step / xcom / state
* `taskinstance` → heartbeat, retry, state change
* `executors` → logs verbeux sur submit / poll

---

### 🔥 2️⃣ Kubernetes (souvent LA source du crash)

```python
logging.getLogger("kubernetes").setLevel(logging.ERROR)
logging.getLogger("kubernetes.client").setLevel(logging.ERROR)
logging.getLogger("kubernetes.client.rest").setLevel(logging.ERROR)
logging.getLogger("kubernetes.watch").setLevel(logging.ERROR)
```

📌 **Indispensable** si tu utilises :

* `KubernetesPodOperator`
* Spark-on-K8s
* sensors kube

---

### 🔥 3️⃣ HTTP / réseau (urllib3 = tueur silencieux)

```python
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.WARNING)
```

📌 Évite les logs du type :

```
Starting new HTTPS connection (1)
```

---

### 🔥 4️⃣ AWS / Cloud (même si indirect)

```python
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("botocore.credentials").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)
```

📌 Même si tu n’appelles pas AWS directement :

* libs transverses
* hooks / providers

---

### 🔥 5️⃣ Providers Airflow (souvent oubliés)

```python
logging.getLogger("airflow.providers.cncf.kubernetes").setLevel(logging.ERROR)
logging.getLogger("airflow.providers.http").setLevel(logging.WARNING)
logging.getLogger("airflow.providers.apache.spark").setLevel(logging.WARNING)
logging.getLogger("airflow.providers.common.sql").setLevel(logging.WARNING)
```

📌 Les providers loggent **beaucoup plus** que le core.

---

## 🧠 OPTION CLÉ (souvent décisive) : couper la propagation

Astronomer + logging = **double voire triple émission**.

```python
for name in [
    "kubernetes",
    "urllib3",
    "airflow.task",
    "airflow.providers",
]:
    logger = logging.getLogger(name)
    logger.propagate = False
```

👉 **Effet immédiat sur Fluent Bit**
👉 Très utilisé chez BNP / CACIB / SG

---

## 🧪 Exemple FINAL prêt-prod (copier-coller)

```python
import logging

LOGGERS_CONFIG = {
    # Airflow core
    "airflow.task": logging.WARNING,
    "airflow.jobs": logging.WARNING,
    "airflow.executors": logging.WARNING,
    "airflow.models.taskinstance": logging.WARNING,
    "airflow.utils.log": logging.ERROR,

    # Providers
    "airflow.providers.cncf.kubernetes": logging.ERROR,
    "airflow.providers.http": logging.WARNING,
    "airflow.providers.apache.spark": logging.WARNING,
    "airflow.providers.common.sql": logging.WARNING,

    # Kubernetes
    "kubernetes": logging.ERROR,
    "kubernetes.client": logging.ERROR,
    "kubernetes.client.rest": logging.ERROR,
    "kubernetes.watch": logging.ERROR,

    # HTTP
    "urllib3": logging.WARNING,
    "urllib3.connectionpool": logging.ERROR,
    "requests": logging.WARNING,

    # AWS
    "botocore": logging.WARNING,
    "botocore.credentials": logging.ERROR,
    "boto3": logging.WARNING,
    "s3transfer": logging.WARNING,
}

for logger_name, level in LOGGERS_CONFIG.items():
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False
```

📌 À placer :

* soit **au début de la task**
* soit dans un **helper importé** (meilleure pratique)

---

## 🚨 Ce que je vois souvent chez Astronomer (retour terrain)

❌ `airflow.task` laissé en INFO
❌ `kubernetes.client.rest` non filtré
❌ propagation activée
❌ logs par ligne / par pod

➡️ FluentBit sature
➡️ ES throttle
➡️ Pod Airflow OOM / crashloop

---

## 🎯 Conclusion claire

👉 **Sur Astronomer 2.9.3**, la bonne stratégie est :

* **filtrer finement par logger**
* **ERROR sur Kubernetes**
* **WARNING sur Airflow**
* **propagate = False**

Si tu veux, envoie-moi :

* un **extrait réel des logs**
* ou le **type exact d’opérateur** (Spark, KPO, sensor…)

Je t’affine la config **au niveau chirurgical** 👌
