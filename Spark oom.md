Voici une **synthèse exploitable côté client**, basée uniquement sur les faits visibles dans tes captures, sans hypothèses inutiles.

---

# Synthèse d’analyse incident Spark

## Symptômes observés

Le job Spark a échoué avec les erreurs suivantes :

```text
ExecutorLostFailure
exit code 137 (OOMKilled)

MetadataFetchFailedException:
Missing an output location for shuffle partition
```

Ces messages indiquent qu’un executor a été arrêté pour dépassement mémoire pendant une phase de shuffle, entraînant la perte des données intermédiaires nécessaires à la poursuite du traitement.

---

# Analyse technique

## 1. Volume traité

D’après Spark UI :

```text
Input total ≈ 19.5 GiB
156 tasks
128 MiB par partition
Shuffle Write ≈ 2.1 GiB
```

La distribution des partitions est homogène :

```text
Median Input Size = Max Input Size
Durations homogènes
```

👉 **Aucun data skew détecté**

Le problème ne provient donc pas d’un déséquilibre des données.

---

## 2. Présence d’un shuffle

Le plan physique montre :

```text
Scan CSV
→ Project
→ Exchange
→ WriteFiles
```

L’opérateur :

```text
Exchange
```

indique une phase de redistribution des données (shuffle), nécessaire avant l’écriture.

Ce comportement est normal et attendu dans ce type de traitement.

---

## 3. Cause principale identifiée

Un executor a été perdu avec :

```text
OOMKilled (exit code 137)
```

Conséquence :

```text
MetadataFetchFailedException
```

Cela signifie :

```text
Executor tué → fichiers shuffle perdus → job échoue
```

Cause racine probable :

```text
Mémoire executor insuffisante
pendant phase shuffle + écriture parquet
```

---

## 4. Facteur aggravant identifié

Lecture initiale en :

```text
CSV
```

Le format CSV :

```text
✔ parsing texte coûteux
✔ plus de mémoire temporaire
✔ plus de pression CPU/mémoire
```

Cela augmente la pression mémoire pendant le shuffle.

---

# Dimensionnement mémoire estimé

Configuration actuelle :

```text
spark.executor.instances = 4
spark.executor.memory = 4g
memoryOverhead ≈ 400–500 MB (défaut)
```

Mémoire totale actuelle :

```text
≈ 18–20 GiB
```

Insuffisant pour ce volume.

---

## Dimensionnement recommandé

### Minimum recommandé

```text
spark.executor.instances=4
spark.executor.memory=6g
spark.executor.memoryOverhead=2g
```

Total mémoire :

```text
≈ 32 GiB
```

---

### Dimensionnement cible (plus robuste)

```text
spark.executor.instances=4
spark.executor.memory=8g
spark.executor.memoryOverhead=2g
```

Total mémoire :

```text
≈ 40 GiB
```

---

# Optimisations recommandées

## 1. Augmenter le parallélisme shuffle

```text
spark.sql.shuffle.partitions=200
```

Objectif :

```text
Réduire taille mémoire par partition
Limiter risque OOM
```

---

## 2. Réduire volume avant shuffle

À valider côté code :

```text
✔ appliquer les filtres le plus tôt possible
✔ sélectionner uniquement les colonnes nécessaires
✔ éviter repartition inutile
```

---

## 3. Optimisation structurelle recommandée

Si les données sources sont en CSV volumineux :

```text
Mettre en place une étape initiale
CSV → Parquet
```

Objectif :

```text
✔ réduire taille des données
✔ réduire pression mémoire
✔ améliorer stabilité des traitements
```

---

# Conclusion technique

Le job a échoué suite à :

```text
Perte d’un executor (OOMKilled)
pendant une phase normale de shuffle
```

Facteurs contributifs identifiés :

```text
✔ Mémoire executor sous-dimensionnée
✔ Shuffle sur volume significatif (~20 GiB)
✔ Lecture initiale au format CSV
```

Aucun déséquilibre des données (data skew) n’a été observé.

---

# Formulation courte prête pour ticket

> L’analyse montre que l’échec du job est dû à la perte d’un executor en `OOMKilled` durant une phase de shuffle. Cette perte a entraîné une indisponibilité des données intermédiaires (`MetadataFetchFailedException`). La distribution des partitions est homogène, ce qui exclut un problème de data skew. La configuration mémoire actuelle (4 executors × 4g) apparaît sous-dimensionnée pour le volume traité (~19.5 GiB). Un dimensionnement autour de 32 à 40 GiB au total côté executors est recommandé, ainsi qu’un ajustement du parallélisme shuffle et une optimisation de la lecture des données sources (CSV).
