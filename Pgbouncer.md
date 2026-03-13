Voici **deux versions** comme tu l’as demandé :

1️⃣ **Synthèse complète avec les chiffres** (pour analyse interne / client technique)
2️⃣ **Message court à ajouter dans le ticket**

---

# 1️⃣ Synthèse globale de l’analyse

## Contexte

Lors de l’exécution de certains DAGs Airflow, l’erreur suivante est observée :

```text
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

Cette erreur indique que **la limite maximale de connexions PostgreSQL est atteinte**, empêchant l’ouverture de nouvelles connexions.

---

# Configuration PostgreSQL

Paramètres observés sur le serveur :

| Paramètre                      | Valeur |
| ------------------------------ | ------ |
| max_connections                | 115    |
| superuser_reserved_connections | 15     |

Connexions applicatives disponibles :

```
115 - 15 = 100 connexions
```

---

# Architecture observée

L’environnement du client comporte :

* **19 instances Astronomer / Airflow**
* chaque instance dispose de **sa propre base PostgreSQL**
* toutes les bases sont hébergées sur **le même serveur PostgreSQL**

L’accès à la base est réalisé via **PgBouncer**, configuré en :

```
pool_mode = transaction
```

Les pods Airflow utilisent bien PgBouncer via :

```
DATABASE_HOST = pgbouncer
DATABASE_PORT = 6432
```

---

# Configuration Airflow

Paramètres observés :

```
sql_alchemy_pool_enabled = True
sql_alchemy_pool_size = 5
```

Cette configuration limite le **pool SQLAlchemy par processus Airflow**, mais une instance Airflow comporte plusieurs processus :

* scheduler
* webserver
* triggerer
* workers (pods de tâches)

---

# Analyse des connexions

Requête utilisée :

```sql
select datname, usename, count(*) as connections
from pg_stat_activity
group by datname, usename
order by connections desc;
```

Résultat observé :

* chaque instance Astronomer utilise environ **5 à 8 connexions PostgreSQL**
* avec **19 instances**, le volume total atteint environ :

```
19 × 6 connexions ≈ 114 connexions
```

Cela dépasse la capacité applicative actuelle :

```
100 connexions disponibles
```

---

# Comportement des pods de tâches

Lors de l’exécution d’un DAG :

* Airflow crée des **pods Kubernetes dédiés pour les tâches**
* ces pods accèdent également à la **metadata database Airflow**
* ils ouvrent temporairement **1 à 2 connexions supplémentaires**

Ces connexions passent également par **PgBouncer**.

---

# Conclusion technique

L’incident est dû à une **saturation du nombre maximal de connexions PostgreSQL**.

Même si :

* PgBouncer est correctement configuré
* Airflow utilise un pool SQLAlchemy limité

le nombre d’instances Astronomer (19) utilisant simultanément le même serveur PostgreSQL entraîne une consommation globale de connexions proche ou supérieure à la limite actuelle.

---

# Recommandation

La limite actuelle :

```
max_connections = 115
```

est insuffisante pour cet environnement.

Une valeur plus adaptée serait :

```
max_connections = 200 à 250
```

Cette modification permettrait :

* d’absorber la charge actuelle
* d’éviter les erreurs de saturation
* de conserver une marge pour la croissance des DAGs et des workers.

---

# 2️⃣ Texte court à ajouter dans le ticket

Voici une **version synthétique pour le ticket** :

---

L’analyse montre que l’erreur rencontrée est liée à une saturation du nombre maximal de connexions PostgreSQL.

Le serveur est actuellement configuré avec :

* `max_connections = 115`
* `superuser_reserved_connections = 15`

soit **100 connexions applicatives disponibles**.

L’environnement comporte **19 instances Astronomer**, chacune ouvrant environ **5 à 8 connexions simultanées** vers PostgreSQL.
La consommation totale atteint donc environ **110 connexions**, ce qui dépasse la limite actuelle.

PgBouncer est correctement configuré (`pool_mode = transaction`) et les connexions Airflow passent bien par celui-ci.

Afin d’éviter ce type d’incident, il est recommandé d’augmenter la valeur de `max_connections` (par exemple **200 à 250**) afin d’adapter la capacité du serveur à la charge actuelle de la plateforme.

---

Si tu veux, je peux aussi te faire **une version encore plus “support enterprise / client premium”** (celle que les équipes SRE envoient généralement aux gros clients) qui est **plus diplomatique et moins prescriptive**.
