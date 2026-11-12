# Checklist technique N2 – Upgrade PostgreSQL Metadata Airflow



DataHub V2 – DMZR IBM

Type d'upgrade à confirmer



Périmètre : bases PostgreSQL Metadata utilisées par Airflow, avec PgBouncer comme intermédiaire.

L'objectif est de vérifier trois choses :

1. Airflow ne perd pas durablement sa connexion à PostgreSQL.
2. Les composants Airflow reprennent correctement après les interruptions.
3. Les DAGs et les traitements planifiés continuent à fonctionner normalement.

Je te propose une checklist directement exploitable pendant une opération de changement.

## 1. Identifier précisément le changement

Avant toute intervention, demander à l'équipe IBM :

| Information                 | À obtenir                             |
| --------------------------- | ------------------------------------- |
| Version actuelle PostgreSQL | Ex. 15.x                              |
| Version cible               | Ex. 16.x ou patch                     |
| Type de changement          | Major / Minor / Maintenance           |
| Date et fenêtre             | Début et fin prévues                  |
| Durée estimée               | Indisponibilité prévue                |
| Endpoint                    | Identique ou modifié                  |
| Certificat TLS              | Modification ou non                   |
| PgBouncer                   | Redémarrage ou reconnexion nécessaire |
| HA / Failover               | Comportement prévu                    |
| Rollback                    | Procédure de récupération             |

Point de vigilance : ne considère pas automatiquement un In-place Change Upgrade comme un simple patch. Un upgrade majeur PostgreSQL peut provoquer une période read-only, une indisponibilité complète et plusieurs coupures de sessions clientes.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://cloud.ibm.com\&sz=32)

IBM Cloud Docs+1



## 2. Contrôles avant upgrade

Avant changement

### A. Kubernetes – État des composants Airflow

Exécuter sur le namespace Airflow concerné :

```
kubectl get pods -n <namespace>
```

Vérifier :

- Scheduler : Running / Ready.
- Webserver ou API Server : Running / Ready.
- DAG Processor : Running / Ready.
- Workers : Running / Ready.
- Aucun CrashLoopBackOff.
- Aucun redémarrage anormal.

Contrôler les Deployments :

```
kubectl get deployments -n <namespace>
```

### B. PgBouncer

- Pod PgBouncer opérationnel.
- Pas d'erreur de connexion PostgreSQL.
- Pas de saturation du pool.
- Connexions disponibles.
- Pas de hausse anormale des timeouts.

Si la console PgBouncer est accessible :

```
SHOW POOLS;
SHOW STATS;
SHOW SERVERS;
SHOW CLIENTS;
```

Ces commandes sont à exécuter sur la console d'administration PgBouncer, pas sur PostgreSQL.

### C. Airflow – Logs de référence

Récupérer les logs avant changement :

```
kubectl logs <scheduler-pod> -n <namespace> --since=30m
```

```
kubectl logs <dag-processor-pod> -n <namespace> --since=30m
```

Rechercher notamment :

```
OperationalError
psycopg2.OperationalError
connection timeout
server closed the connection unexpectedly
SSL connection has been closed unexpectedly
```

- Pas d'erreur PostgreSQL persistante.
- Scheduler heartbeat normal.
- DAG parsing normal.
- Aucun DAG bloqué anormalement.

## 3. Contrôles pendant l'upgrade

Pendant changement

C'est ici que tu dois surveiller les interactions entre PostgreSQL, PgBouncer et Airflow.

### A. Surveillance Kubernetes

```
kubectl get pods -n <namespace> -w
```

Surveiller les événements :

```
kubectl get events -n <namespace> \
  --sort-by=.lastTimestamp
```

- Les composants Airflow ne redémarrent pas en boucle.
- Les pods restent dans un état cohérent.
- Les éventuels redémarrages sont identifiés.
- PgBouncer retrouve son backend PostgreSQL.

### B. Surveillance des logs

Sur le Scheduler et les Workers, rechercher :

| Erreur                           | Signification                             |
| -------------------------------- | ----------------------------------------- |
| `connection refused`             | PostgreSQL indisponible                   |
| `57P01`                          | Arrêt administratif de session PostgreSQL |
| `25006`                          | Transaction en lecture seule              |
| `too many connections`           | Limite de connexions atteinte             |
| `OperationalError`               | Erreur de connexion côté client           |
| `SSL connection has been closed` | Connexion TLS interrompue                 |

Commandes :

```
kubectl logs <scheduler-pod> -n <namespace> --since=10m
```

```
kubectl logs <worker-pod> -n <namespace> --since=10m
```

### C. Comportement fonctionnel

- Vérifier si le Scheduler continue à envoyer des tâches.
- Vérifier si les tâches en cours rencontrent des erreurs DB.
- Vérifier si les DAG Runs passent en état Failed ou restent bloqués.
- Vérifier si les Workers arrivent à récupérer les nouvelles tâches.

Important : pendant une phase read-only, Airflow peut échouer à écrire les états des tâches, les heartbeats ou les métadonnées. Il faut donc distinguer une interruption attendue d'une panne persistante.

## 4. Contrôles après upgrade

Après changement

### A. PostgreSQL et PgBouncer

Demander à l'équipe IBM de confirmer :

- Upgrade terminé.
- Nouvelle version active.
- Instance PostgreSQL Healthy.
- Membres HA synchronisés.
- Connexions clientes acceptées.
- Écritures réactivées.

Si tu as accès à PostgreSQL :

```
SELECT version();
```

```
SHOW default_transaction_read_only;
```

Résultat attendu pour le second contrôle :

```
off
```

Attention : exécuter cette commande dans une nouvelle session après la reprise.

### B. Vérification Airflow

```
kubectl get pods -n <namespace>
```

Puis vérifier les logs du Scheduler :

```
kubectl logs <scheduler-pod> -n <namespace> --since=15m
```

- Scheduler opérationnel.
- DAG Processor opérationnel.
- Webserver/API accessible.
- Workers opérationnels.
- Plus d'erreurs de connexion PostgreSQL.
- Plus d'erreurs de transaction read-only.

### C. Tests fonctionnels

Je recommande ces quatre tests :

| Test               | Action                         | Résultat attendu         |
| ------------------ | ------------------------------ | ------------------------ |
| Lecture            | Ouvrir un DAG existant         | Informations accessibles |
| Lecture historique | Consulter les anciens DAG Runs | Historique disponible    |
| Écriture           | Déclencher un DAG de test      | DAG Run créé             |
| Exécution          | Exécuter une tâche simple      | Task Success             |

Ne déclenche pas un DAG client en production uniquement pour tester. Utilise un DAG de test sans effet métier.

### D. Vérification de la stabilité

Après la reprise :

- Attendre au moins un cycle de scheduling.
- Vérifier les DAGs planifiés.
- Vérifier les tâches en attente.
- Vérifier les tâches en cours.
- Vérifier les tâches terminées.
- Contrôler les métriques de latence et d'erreurs PostgreSQL.

Je recommande une surveillance renforcée pendant les 30 à 60 minutes suivant la reprise, à adapter à la fréquence des DAGs.

## 5. Les trois contrôles SQL à demander à l'équipe DBA

Si tu n'as pas directement accès à PostgreSQL, demande à l'équipe IBM de fournir ces résultats avant et après l'upgrade.

1\. Version et disponibilité

```
SELECT version();
SHOW default_transaction_read_only;
```

2\. Connexions actives

```
SELECT
    state,
    count(*)
FROM pg_stat_activity
GROUP BY state;
```

3\. Réplication HA

```
SELECT
    application_name,
    state,
    sync_state,
    pg_wal_lsn_diff(
        pg_current_wal_lsn(),
        replay_lsn
    ) AS replay_lag_bytes
FROM pg_stat_replication;
```

Résultat attendu : les membres HA sont en streaming et le retard de réplication revient à zéro.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://cloud.ibm.com\&sz=32)

IBM Cloud Docs



## 6. Tableau de suivi opérationnel N2

Tu peux reprendre directement ce tableau dans ton ticket de changement ServiceNow.

| Contrôle               | Avant | Pendant | Après |
| ---------------------- | ----- | ------- | ----- |
| PostgreSQL Healthy     | X     | X       | X     |
| PgBouncer opérationnel | X     | X       | X     |
| Scheduler              | X     | X       | X     |
| DAG Processor          | X     | X       | X     |
| Workers                | X     | X       | X     |
| Connexions PostgreSQL  | X     | X       | X     |
| Logs sans erreurs DB   | X     | X       | X     |
| DAG Runs fonctionnels  | X     |         | X     |
| Exécution des tâches   | X     |         | X     |
| Historique accessible  | X     |         | X     |
| Réplication HA         | X     |         | X     |

## 7. Les critères de validation du changement



GO

&#x20;Changement validé si :



- PostgreSQL est disponible et accepte les écritures.
- PgBouncer a retrouvé ses connexions.
- Tous les composants Airflow sont opérationnels.
- Aucun problème persistant de connexion à PostgreSQL.
- Les DAGs planifiés reprennent normalement.
- Un DAG de test termine en Success.
- Les membres HA sont synchronisés.



NO GO

&#x20;Escalade si :



- PostgreSQL reste indisponible ou read-only.
- PgBouncer ne retrouve pas son backend.
- Scheduler incapable de communiquer avec PostgreSQL.
- DAG Runs bloqués ou tâches incapables de mettre à jour leurs états.
- Problème de réplication HA persistant.

Attention : ne demande pas un rollback ou un redémarrage massif des pods Airflow sans diagnostic. Pour un upgrade majeur IBM, le retour à l'ancienne version n'est pas possible par simple downgrade in-place.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://cloud.ibm.com\&sz=32)

IBM Cloud Docs



## 8. Documentation IBM de référence

[IBM Cloud – PostgreSQL In-place Major Version Upgrade](https://cloud.ibm.com/docs/databases-for-postgresql?topic=databases-for-postgresql-upgrading\&utm_source=chatgpt.com).

C'est la documentation à transmettre à l'équipe DBA pour confirmer le comportement exact de l'opération.

Ma recommandation : en tant que N2 DataHub V2, concentre ton intervention sur la chaîne suivante :

Airflow Scheduler / Workers

PgBouncer

PostgreSQL Metadata – IBM DMZR

C'est cette chaîne qui doit être surveillée en priorité. Les bases PostgreSQL des applications clientes ne font pas partie du périmètre de cet upgrade.

Tu peux également me transmettre le plan de changement IBM (MOP) lorsqu'il sera disponible : je pourrai identifier les risques précis pour Airflow et adapter cette checklist aux étapes réelles de l'intervention.
