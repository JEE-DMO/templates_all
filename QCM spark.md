Voici une proposition **9 questions**, calibrées pour un recrutement **Airflow + Spark en environnement DataOps/MCO bancaire**.

Sources de référence : Airflow définit les tasks comme unités d’exécution dans les DAGs et le dynamic task mapping comme création de tâches à runtime ; Spark AQE optimise notamment les joins, les partitions post-shuffle et les joins skewés. ([Apache Airflow][1]) ([Apache Airflow][2]) ([spark.apache.org][3])

---

## Niveau confirmé

### Q1 — Airflow : retries et idempotence

Un DAG Airflow lance un job Spark qui écrit dans une table partitionnée par `business_date`. Le task Airflow échoue après l’écriture Spark, puis est relancé automatiquement.

Quelle est la meilleure conception ?

A. Désactiver les retries Airflow pour éviter les doublons
B. Garder les retries, mais rendre l’écriture Spark idempotente sur la partition cible
C. Utiliser uniquement `depends_on_past=True`
D. Augmenter `execution_timeout`

**Réponse : B**

Évalue : compréhension retries, idempotence, production.

---

### Q2 — Spark : cache vs persist

Un DataFrame est utilisé deux fois dans le même job Spark après une lecture coûteuse et plusieurs transformations.

Quelle affirmation est la plus correcte ?

A. `cache()` accélère toujours le job
B. `cache()` est utile seulement si une action est appelée avant réutilisation
C. `persist()` force immédiatement le stockage mémoire
D. `cache()` évite tous les shuffles suivants

**Réponse : B**

Évalue : lazy evaluation, cache réel, actions Spark.

---

### Q3 — Airflow : XCom

Un candidat propose de passer un DataFrame Spark complet entre deux tasks Airflow via XCom.

Quelle réponse est correcte ?

A. Bonne pratique si le DataFrame est sérialisable
B. Acceptable uniquement avec KubernetesExecutor
C. Mauvaise pratique : XCom doit contenir des métadonnées légères, pas des données volumineuses
D. Correct si le backend XCom est PostgreSQL

**Réponse : C**

Évalue : séparation orchestration / traitement data.

---

## Niveau senior

### Q4 — Airflow : scheduling

Un DAG quotidien doit traiter les données du 2026-05-31. Le run démarre le 2026-06-01 à 02:00.

Dans le code, quelle date métier faut-il privilégier ?

A. `datetime.now()`
B. `execution_date` / logical date ou `data_interval_start` selon le besoin
C. La date système du worker Kubernetes
D. La date du fichier le plus récent dans le bucket

**Réponse : B**

Évalue : data interval, reproductibilité, backfill.

---

### Q5 — Spark : broadcast join

Une table de référence de 50 Mo est jointe avec une table de faits de plusieurs To. Le job est lent avec beaucoup de shuffle.

Quelle stratégie est la plus pertinente ?

A. `repartition(1)` avant le join
B. Broadcast de la table de référence si elle tient raisonnablement en mémoire executor
C. Cache de la table de faits avant le join
D. Augmenter uniquement `spark.sql.shuffle.partitions`

**Réponse : B**

Évalue : join strategy, shuffle, volumétrie.

---

### Q6 — Airflow + Spark on Kubernetes

Un DAG Airflow lance un SparkApplication sur Kubernetes. Le task Airflow passe en succès dès que la ressource SparkApplication est créée, mais le job Spark échoue ensuite.

Quelle correction est la plus pertinente ?

A. Ajouter `retries=3` sur le task Airflow uniquement
B. Faire attendre Airflow jusqu’à l’état terminal réel du SparkApplication
C. Mettre `depends_on_past=True`
D. Réduire le nombre d’executors Spark

**Réponse : B**

Évalue : orchestration réelle vs soumission de job.

---

## Niveau expert

### Q7 — Spark : AQE et skew

Un join Spark est lent. Le Spark UI montre quelques tasks très longues, alors que la majorité termine rapidement. Les données sont fortement déséquilibrées sur certaines clés.

Quelle option est la plus juste ?

A. Augmenter massivement le nombre d’executors suffit généralement
B. Activer/tuner AQE skew join peut aider, mais il faut aussi analyser les clés skewées
C. Faire `coalesce(1)` avant le join réduit le skew
D. Désactiver AQE pour stabiliser le plan

**Réponse : B**

Évalue : skew, AQE, diagnostic Spark UI.

---

### Q8 — Airflow : dynamic task mapping

Un DAG doit traiter une liste de namespaces Kubernetes récupérée à runtime depuis une API control-plane.

Quelle approche est la plus propre ?

A. Générer dynamiquement le fichier Python du DAG à chaque exécution
B. Utiliser Dynamic Task Mapping pour créer les tasks à runtime à partir de la liste récupérée
C. Créer 500 tasks statiques, une par namespace possible
D. Utiliser une boucle `for` dans le DAG avec un appel API au parse time

**Réponse : B**

Évalue : parse time vs runtime, dynamic mapping.

---

### Q9 — Spark : small files et écriture partitionnée

Un job Spark écrit chaque jour des milliers de petits fichiers Parquet par partition métier. Les lectures deviennent lentes.

Quelle solution est la plus pertinente ?

A. `coalesce(1)` systématique avant écriture
B. Contrôler le nombre de partitions avant écriture et compacter périodiquement les partitions concernées
C. Désactiver Parquet compression
D. Lire les fichiers avec `recursiveFileLookup=true`

**Réponse : B**

Évalue : small files, partitioning, performance long terme.

---

## Variante Codingame

Je recommande :

* **3 questions confirmé**
* **3 questions senior**
* **3 questions expert**
* Temps cible : **25 à 35 minutes**
* Barème :

  * Confirmé : 1 point
  * Senior : 2 points
  * Expert : 3 points
* Score attendu :

  * 0–5 : insuffisant
  * 6–10 : confirmé
  * 11–15 : senior
  * 16–18 : expert solide

Le plus discriminant : **Q3, Q6, Q7, Q8, Q9**.

[1]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html?utm_source=chatgpt.com "Tasks — Airflow 3.2.2 Documentation"
[2]: https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html?utm_source=chatgpt.com "Dynamic Task Mapping — Airflow 3.2.2 Documentation"
[3]: https://spark.apache.org/docs/latest/sql-performance-tuning.html?utm_source=chatgpt.com "Performance Tuning - Spark 4.1.2 Documentation"
