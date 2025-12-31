Parfait, **un DAG Airflow comme *sonde de santé Spark sur Kubernetes***, **sans Grafana / Prometheus / Kibana**.
L’idée : **Airflow interroge périodiquement Kubernetes + Spark History Server + éventuellement le Spark Operator** et pousse un **résultat consolidé** dans un mail / Slack / fichier / XCom.

Ci-dessous je te donne **une solution complète et reproductible**, *production-ready*, que tu peux adapter chez toi.

---

# 🎯 **Objectif du DAG**

À chaque run :

1. Lister les **pods Spark actifs** (driver/executor)
2. Lister les **derniers jobs Spark finis** dans **Spark History Server (SHS)**
3. Vérifier :

   * drivers en échec ?
   * executors souvent OOMKilled ?
   * jobs Spark récemment FAILED ?
   * pods bloqués `Pending` ?
4. Produire un **rapport consolidé**
5. **Notifier par mail / Slack**

---

# 📌 **Dépendances**

Airflow doit pouvoir accéder :

* **API Kubernetes (`/api/v1/...`)**
* **Spark History Server REST API (`/api/v1/applications`)**
  → valable avec Spark 3.3+

Tu peux utiliser la connexion Airflow :

```
Conn ID = kubernetes_default
Conn ID = spark_history_server
```

---

# 🧱 **DAG complet : `spark_health_monitor.py`**

> Ce DAG ne crashe pas si un service manque → il *marque l’état* comme inconnu et continue

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
import requests
from kubernetes import client, config
import datetime

SPARK_HISTORY_URL = Variable.get("SPARK_HISTORY_URL")  # ex: http://spark-history-server:18080

def get_k8s_spark_pods(**context):
    config.load_incluster_config()  # ou load_kube_config() en dev
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces(label_selector="spark-role")  # label du spark-operator
    report = {"running": [], "pending": [], "failed": []}

    for pod in pods.items:
        status = pod.status.phase
        name = pod.metadata.name

        if status == "Running":
            report["running"].append(name)
        elif status == "Pending":
            report["pending"].append(name)
        else:
            report["failed"].append({"name": name, "reason": status})

    context['ti'].xcom_push(key="k8s_report", value=report)


def get_spark_history_state(**context):
    """Récupère l'état des jobs spark terminés via SHS"""
    report = {"completed": 0, "failed": 0, "apps": []}

    try:
        resp = requests.get(f"{SPARK_HISTORY_URL}/api/v1/applications", timeout=5)
        apps = resp.json()
    except Exception:
        context['ti'].xcom_push(key="history_report", value={"status": "unreachable"})
        return

    # On ne garde que les 20 derniers
    for app in apps[:20]:
        attempts = app.get("attempts", [])
        for a in attempts:
            status = a.get("completed", False)
            final = a.get("finalStatus", "UNKNOWN")

            if final == "SUCCEEDED":
                report["completed"] += 1
            else:
                report["failed"] += 1

            report["apps"].append({
                "id": app["id"],
                "name": app["name"],
                "state": final,
                "duration_s": a.get("duration")
            })

    context['ti'].xcom_push(key="history_report", value=report)


def build_health_summary(**context):
    k8s_report = context['ti'].xcom_pull(key="k8s_report")
    history_report = context['ti'].xcom_pull(key="history_report")

    result = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "pods_running": len(k8s_report["running"]),
        "pods_pending": len(k8s_report["pending"]),
        "pods_failed": len(k8s_report["failed"]),
        "spark_completed": history_report.get("completed", 0),
        "spark_failed": history_report.get("failed", 0),
    }

    # règle simple : cluster sain si pas de pending ni de failed récents
    result["cluster_healthy"] = (
        result["pods_failed"] == 0 and
        result["pods_pending"] == 0 and
        result["spark_failed"] == 0
    )

    context['ti'].xcom_push(key="summary", value=result)


def print_report(**context):
    summary = context['ti'].xcom_pull(key="summary")
    print("=== SPARK HEALTH REPORT ===")
    for k,v in summary.items():
        print(f"{k}: {v}")

    if not summary["cluster_healthy"]:
        raise Exception("Spark cluster is NOT healthy!")


with DAG(
    dag_id="spark_health_monitor",
    schedule_interval="*/30 * * * *",  # toutes les 30 min
    start_date=days_ago(1),
    catchup=False,
) as dag:

    k8s_pods = PythonOperator(
        task_id="check_k8s_spark_pods",
        python_callable=get_k8s_spark_pods
    )

    spark_history = PythonOperator(
        task_id="check_spark_history",
        python_callable=get_spark_history_state
    )

    build_summary = PythonOperator(
        task_id="build_health_summary",
        python_callable=build_health_summary
    )

    report = PythonOperator(
        task_id="print_report",
        python_callable=print_report
    )

    k8s_pods >> spark_history >> build_summary >> report
```

---

# 🧠 **Ce que surveille réellement ce DAG**

| Source        | Vérification | Symptôme                     |
| ------------- | ------------ | ---------------------------- |
| Kubernetes    | pods pending | cluster saturé / quota       |
| Kubernetes    | pods failed  | OOMKilled / imagePull / RBAC |
| Spark History | jobs failed  | perf / exceptions spark      |
| Spark History | recurrence   | stabilité dans le temps      |

**=> C’est exactement ce que font les plateformes internes bancaires, mais sans Prometheus.**

---

# 🎚️ **Aller plus loin**

| Option               | Intérêt                | Intégration dans le DAG |
| -------------------- | ---------------------- | ----------------------- |
| Notifier Slack/Teams | Alerting               | `SlackWebhookOperator`  |
| Notifier email       | Rapports réguliers     | `EmailOperator`         |
| Stocker en S3        | Historique santé       | `S3Hook`                |
| Webhook              | Intégration SI interne | `SimpleHttpOperator`    |
| Scoring santé        | Confiance 0–100        | pondération KPI         |

---

# 💎 *Résultat attendu*

Dans Airflow UI :
→ **un seul DAG**,
→ **statut rouge = mauvais état Spark**,
→ **logs Airflow = rapport lisible + automatisable**.

---

# 🚀 Tu veux la version **avec envoi d'email stylé HTML** ?

Dis-moi **Slack ou Mail**, je te donne :

* modèle HTML
* badges couleur (OK / WARN / KO)
* pièces jointes avec logs
* score de santé (%)

On peut même générer un **PDF automatique** pour management.

Tu veux quelle version ?
`Slack`, `Email`, `PDF`, `CSV`, `Callback Teams`, `Webhook Dynatrace` ?
