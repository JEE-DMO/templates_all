Des incohérences de remontée des métriques CPU/Memory (requests/limits) ont été constatées dans Dynatrace pour les jobs Spark.

L’analyse a mis en évidence un contexte de forte volumétrie de pods pouvant impacter la collecte des métriques Kubernetes.

Une action d’ajustement de la configuration deleteOldPods a été engagée afin de réduire la rétention des pods et limiter cet impact.

Un suivi est en cours via un incident Dynatrace associé.
