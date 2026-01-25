Parfait Djamel — là tu es exactement au bon endroit :
le mail HTML c’est bien pour le *report global*, mais Teams doit servir uniquement pour les **alertes actionnables** → uniquement les tenants **unhealthy**.

Je te propose un design propre, scalable et “Airflow-like” :

✅ Filtrer tes `SparkTenant` unhealthy
✅ Construire une Adaptive Card par tenant (ou un batch)
✅ Envoyer vers Teams via Incoming Webhook

---

# ✅ Objectif

👉 Envoyer une alerte Teams uniquement pour :

* `health_status != Healthy`
* ou `all_healthy == False`

Exemple :

* 🔴 Unhealthy
* 🟠 Missing
* ⚠️ Degraded
* ❓ Unknown

---

# ✅ Script Python complet (Production Ready)

## 1. Dependencies

```bash
pip install requests
```

---

## 2. Script Teams Alert Spark Tenants

```python
import requests
import json


# =============================
# CONFIG
# =============================

TEAMS_WEBHOOK_URL = "https://outlook.office.com/webhook/XXXX..."

STATUS_COLOR = {
    "Healthy": "Good",
    "Progressing": "Warning",
    "Degraded": "Attention",
    "Missing": "Attention",
    "Unknown": "Warning",
    "Unhealthy": "Attention"
}


# =============================
# FILTER UNHEALTHY TENANTS
# =============================

def filter_unhealthy(tenants):
    return [t for t in tenants if not t.all_healthy]


# =============================
# ADAPTIVE CARD BUILDER
# =============================

def build_tenant_card(tenant):
    """
    Build Adaptive Card JSON for one Spark Tenant
    """

    health = tenant.health_status
    sync = tenant.sync_status

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": [

            # Title
            {
                "type": "TextBlock",
                "text": f"🚨 Spark Tenant Unhealthy - {tenant.environment.upper()}",
                "weight": "Bolder",
                "size": "Large",
                "color": "Attention"
            },

            # Main Info
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Tenant:", "value": tenant.tenant_name},
                    {"title": "Business Line:", "value": tenant.business_line},
                    {"title": "Health Status:", "value": health},
                    {"title": "Sync Status:", "value": sync},
                    {"title": "Version:", "value": tenant.sparkaas_version},
                    {"title": "Cluster:", "value": tenant.cluster_name},
                    {"title": "IBM Account:", "value": tenant.ibm_account},
                ]
            },

            # Deprecated flag
            {
                "type": "TextBlock",
                "text": f"⚠️ Deprecated Version: {tenant.deprecated_msg}"
                if tenant.is_deprecated_version else "",
                "wrap": True,
                "color": "Warning",
                "isVisible": tenant.is_deprecated_version
            }
        ],

        # Action button (Spark UI)
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Open Spark UI",
                "url": tenant.spark_ui_url
            }
        ]
    }


# =============================
# SEND CARD TO TEAMS
# =============================

def send_card_to_teams(card_json):

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_json
            }
        ]
    }

    response = requests.post(
        TEAMS_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )

    if response.status_code != 200:
        raise Exception(
            f"Teams webhook failed: {response.status_code} {response.text}"
        )


# =============================
# MAIN ALERT PROCESS
# =============================

def alert_unhealthy_tenants(tenants):

    unhealthy = filter_unhealthy(tenants)

    if not unhealthy:
        print("✅ All Spark Tenants Healthy. No Teams alert sent.")
        return

    print(f"🚨 {len(unhealthy)} unhealthy tenants detected!")

    for tenant in unhealthy:
        card = build_tenant_card(tenant)
        send_card_to_teams(card)

        print(f"✅ Alert sent for tenant: {tenant.tenant_name}")
```

---

# ✅ Usage Exemple dans ton DAG Airflow

```python
from mymodule.teams_alert import alert_unhealthy_tenants

def task_send_teams_alert(**context):

    tenants = context["ti"].xcom_pull(
        key="spark_tenants",
        task_ids="fetch_spark_status"
    )

    alert_unhealthy_tenants(tenants)
```

---

# ✅ Output Teams (Design recommandé)

Teams recevra une carte type :

🚨 Spark Tenant Unhealthy - DEV

* Tenant : spark-ap12345
* Health : Missing
* Sync : OutOfSync
* Version : 4.0
* Cluster : iks-ap12345
  ✅ Bouton : Open Spark UI

---

# ✅ Variante (1 seule card avec tous les unhealthy tenants)

Si tu veux éviter spam Teams :

✅ Une seule AdaptiveCard avec liste des unhealthy

Je peux te faire la version “batch summary card”.

---

# ✅ Prochaine étape idéale

Tu peux faire exactement comme Airflow :

* Spark global mail HTML (daily report)
* Teams alert only on unhealthy (action immediate)
* Jira creation auto si persistant 3 runs

---

# 🔥 Question rapide

Tu préfères :

1. **1 card par tenant unhealthy** (plus actionnable)
2. **1 card unique résumée** (moins de bruit Teams)

Je te génère directement le template Adaptive Designer correspondant.
