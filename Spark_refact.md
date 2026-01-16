Yes, ton intuition est **très bonne** 👍
Là tu es pile sur un problème classique : **une fonction métier (aggregate)** trop **couplée à un modèle technique** (HealthStatus Airflow), alors que ton besoin réel est beaucoup plus simple.

👉 **Ce que ta fonction utilise vraiment**, si on résume froidement :

Dans `aggregate_health_summary`, tu n’utilises que :

* `environment`
* `business_line`
* `is_all_healthy` (bool)

Le reste du modèle Airflow est **totalement inutile** pour l’agrégation.

---

## 🎯 Objectif cible (clean & réutilisable)

👉 Avoir **UNE fonction d’agrégation générique**, indépendante :

* de Airflow
* de Spark
* de Kubernetes
* de tout modèle métier

👉 Et **DEUX adapters** :

* Airflow → modèle commun
* Spark → modèle commun

---

## 🧠 Pattern recommandé : **DTO / Projection minimale**

### 1️⃣ Crée un modèle ultra-minimal (le vrai contrat)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class HealthAggregateItem:
    environment: str
    business_line: str
    is_healthy: bool
```

👉 **C’est LE contrat de ta fonction d’agrégation**
Ni plus. Ni moins.

---

### 2️⃣ Refactor de ta fonction `aggregate_health_summary`

```python
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

def aggregate_health_summary(
    items: List[HealthAggregateItem],
) -> Dict[str, Any]:

    total = len(items)
    healthy = sum(item.is_healthy for item in items)

    by_environment = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})
    by_business_line = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})

    for item in items:
        env = item.environment
        bl = item.business_line
        is_healthy = item.is_healthy

        by_environment[env]['total'] += 1
        by_environment[env]['healthy'] += int(is_healthy)
        by_environment[env]['unhealthy'] += int(not is_healthy)

        by_business_line[bl]['total'] += 1
        by_business_line[bl]['healthy'] += int(is_healthy)
        by_business_line[bl]['unhealthy'] += int(not is_healthy)

    return {
        'total_instances': total,
        'healthy_instances': healthy,
        'unhealthy_instances': total - healthy,
        'by_environment': dict(by_environment),
        'by_business_line': dict(by_business_line),
        'checked_at': datetime.now().isoformat()
    }
```

👉 **Zéro dépendance métier**
👉 **Testable en 3 lignes**
👉 **Réutilisable partout**

---

## 3️⃣ Adapter Airflow → HealthAggregateItem

Dans ton code Airflow :

```python
def airflow_to_aggregate_items(
    statuses: list[HealthStatus],
) -> list[HealthAggregateItem]:

    return [
        HealthAggregateItem(
            environment=hs.instance.environment,
            business_line=hs.instance.business_line,
            is_healthy=hs.is_all_healthy,
        )
        for hs in statuses
    ]
```

Usage :

```python
items = airflow_to_aggregate_items(airflow_health_statuses)
summary = aggregate_health_summary(items)
```

---

## 4️⃣ Adapter Spark → HealthAggregateItem

À partir de ton `SparkTenant` :

```python
def spark_to_aggregate_items(
    tenants: list[SparkTenant],
) -> list[HealthAggregateItem]:

    return [
        HealthAggregateItem(
            environment=tenant.environment,
            business_line=tenant.business_line,
            is_healthy=tenant.all_healthy,
        )
        for tenant in tenants
    ]
```

Usage :

```python
items = spark_to_aggregate_items(spark_tenants)
summary = aggregate_health_summary(items)
```

---

## 🔥 Bonus : agrégation **Airflow + Spark ensemble**

```python
items = (
    airflow_to_aggregate_items(airflow_statuses)
    + spark_to_aggregate_items(spark_tenants)
)

summary = aggregate_health_summary(items)
```

👉 Et là tu peux sortir :

* une vision **plateforme**
* une vision **produit**
* une vision **cross-domain**

---

## 🧩 Pourquoi cette approche est solide (BNP-proof 😄)

✔ séparation claire **métier / technique**
✔ aucun if/else dans l’agrégateur
✔ extensible (Kafka, Trino, DB, etc.)
✔ facile à mocker en test
✔ compatible JSON / API / Airflow XCom

---

## 🏁 En une phrase

> **Ton agrégateur ne doit jamais savoir ce qu’est Airflow ou Spark.
> Il doit juste agréger des faits.**

Si tu veux, au prochain message je peux te proposer :

* une version **interface / Protocol**
* ou une version **100% dict / JSON**
* ou un **schéma OpenAPI / contract first**

Dis-moi 👌
