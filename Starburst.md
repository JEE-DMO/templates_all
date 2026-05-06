Oui. Objectif : **prouver la lenteur sur 15 jours** avec des métriques factuelles : volume de requêtes, temps elapsed, CPU, queued time, failed queries, top users, top requêtes.

## 1. D’abord trouver les tables disponibles

À exécuter sur Starburst :

```sql
SHOW CATALOGS;

SHOW SCHEMAS FROM system;

SHOW TABLES FROM system.runtime;
```

Puis chercher les tables de stats/historique :

```sql
SELECT table_catalog, table_schema, table_name
FROM information_schema.tables
WHERE lower(table_name) LIKE '%query%'
   OR lower(table_name) LIKE '%stat%'
   OR lower(table_name) LIKE '%metric%'
ORDER BY 1,2,3;
```

## 2. Si tu as une table d’historique type `query_history`

Exemple générique à adapter selon le vrai nom des colonnes :

```sql
SELECT
    date_trunc('day', create_time) AS day,
    count(*) AS nb_queries,
    count_if(state = 'FAILED') AS nb_failed,
    approx_percentile(elapsed_time_ms / 1000.0, 0.50) AS p50_elapsed_sec,
    approx_percentile(elapsed_time_ms / 1000.0, 0.90) AS p90_elapsed_sec,
    approx_percentile(elapsed_time_ms / 1000.0, 0.95) AS p95_elapsed_sec,
    avg(elapsed_time_ms / 1000.0) AS avg_elapsed_sec,
    sum(cpu_time_ms / 1000.0 / 60.0) AS total_cpu_min
FROM <catalog>.<schema>.<query_history_table>
WHERE create_time >= current_timestamp - interval '15' day
GROUP BY 1
ORDER BY 1;
```

C’est cette requête qui te donne le **graphique principal** :
**jour par jour : nb queries + p95 elapsed + CPU total**.

## 3. Pour prouver une saturation / contention

```sql
SELECT
    date_trunc('hour', create_time) AS hour,
    count(*) AS nb_queries,
    approx_percentile(elapsed_time_ms / 1000.0, 0.95) AS p95_elapsed_sec,
    approx_percentile(queued_time_ms / 1000.0, 0.95) AS p95_queued_sec,
    sum(cpu_time_ms / 1000.0 / 60.0) AS total_cpu_min
FROM <catalog>.<schema>.<query_history_table>
WHERE create_time >= current_timestamp - interval '15' day
GROUP BY 1
ORDER BY 1;
```

À mettre en graphique :

| Métrique                | Interprétation                         |
| ----------------------- | -------------------------------------- |
| `p95_elapsed_sec` monte | lenteur visible utilisateur            |
| `p95_queued_sec` monte  | attente de ressources / cluster saturé |
| `total_cpu_min` monte   | charge CPU élevée                      |
| `nb_queries` monte      | surcharge par volume                   |
| `nb_failed` monte       | instabilité / timeouts / erreurs       |

## 4. Identifier les UID qui consomment le plus

```sql
SELECT
    user,
    count(*) AS nb_queries,
    approx_percentile(elapsed_time_ms / 1000.0, 0.95) AS p95_elapsed_sec,
    sum(cpu_time_ms / 1000.0 / 60.0) AS total_cpu_min,
    sum(processed_input_bytes) / 1024 / 1024 / 1024 AS processed_gb
FROM <catalog>.<schema>.<query_history_table>
WHERE create_time >= current_timestamp - interval '15' day
GROUP BY user
ORDER BY total_cpu_min DESC
LIMIT 20;
```

## 5. Identifier les requêtes KYC les plus lentes

```sql
SELECT
    query_id,
    user,
    create_time,
    state,
    elapsed_time_ms / 1000.0 AS elapsed_sec,
    cpu_time_ms / 1000.0 AS cpu_sec,
    queued_time_ms / 1000.0 AS queued_sec,
    processed_input_bytes / 1024 / 1024 / 1024 AS processed_gb,
    substr(query, 1, 500) AS query_preview
FROM <catalog>.<schema>.<query_history_table>
WHERE create_time >= current_timestamp - interval '15' day
  AND lower(query) LIKE '%kyc%'
ORDER BY elapsed_time_ms DESC
LIMIT 50;
```

## Point important

`system.runtime.queries` donne surtout le **temps réel**, pas forcément l’historique 15 jours. Pour les 15 jours, il te faut une table d’historique Starburst/Trino alimentée par l’event listener ou les tables internes de monitoring.

Phrase utile à envoyer :

> Pour objectiver la lenteur constatée sur la chaîne KYC, nous allons extraire l’historique des requêtes Starburst sur les 15 derniers jours : nombre de requêtes, temps d’exécution P95, temps d’attente en queue, CPU consommé et volume scanné. Cela permettra de distinguer une lenteur liée à la charge globale, à la saturation du cluster, ou à certaines requêtes/utilisateurs spécifiques.
