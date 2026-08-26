Bonjour,

Suite à l’analyse du job Spark sur DHV2, plusieurs éléments ressortent de la Spark UI.

Le traitement, qui s’exécutait en environ **1h30 sur Hadoop**, dépasse actuellement plusieurs heures sur SparkAAS. Nous ne constatons pas de problème particulier de mémoire, de GC, de skew ou d’échec des executors.

En revanche, le workload présente un **très fort niveau de parallélisme à absorber** :

* plus de **1 200 jobs Spark** déclenchés ;
* certains stages comportent **5 712 tasks pour seulement ~4,4 GiB de données** ;
* ces 5 712 partitions sont présentes dès le `FileScan` Parquet ;
* l’application dispose actuellement de seulement **10 executors × 5 cores = 50 cores**.

Les tasks étant courtes (majoritairement quelques secondes), le temps est principalement pénalisé par leur nombre et leur exécution en vagues successives.

On observe également de nombreux appels à `isEmpty()` suivis d’écritures `csv`. Le `isEmpty()` étant fonctionnellement nécessaire pour gérer le cas sans données et générer la ligne technique attendue, une optimisation de cette partie nécessiterait une modification applicative (`persist`, évolution de la gestion de la ligne technique, etc.).

Dans le contexte de la migration, et afin de **limiter au maximum les modifications du traitement**, je propose dans un premier temps :

1. de comparer le sizing Spark actuel avec les ressources utilisées historiquement sur Hadoop ;
2. d’augmenter le nombre d’executors/cores disponibles pour ce traitement et de mesurer le gain ;
3. d’étudier l'utilisation du **Dynamic Allocation** avec un `maxExecutors` adapté, le worker pool étant partagé entre plusieurs tenants.

L’objectif est d’abord de vérifier si un dimensionnement adapté permet de retrouver un temps d’exécution acceptable, avant d'envisager des modifications du code ou du partitionnement.

Cordialement,
Djamel
