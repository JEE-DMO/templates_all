Oui. D’après les captures, le diagnostic est **très direct**.

Le `SparkApplication` est bien créé. Le driver reste en `ContainerCreating` parce que Kubernetes n’arrive pas à monter un volume obligatoire. Le `describe pod` donne explicitement :

> `FailedMount: MountVolume.SetUp failed for volume "hadoop-conf": secret "vm-hadoop-conf" not found`

Donc ce n’est, à ce stade, **ni un problème Spark, ni Airflow, ni un problème nécessitant une investigation N2/N3 Build**. Le pod référence simplement un Secret Kubernetes qui n’existe pas dans le namespace. Et la documentation que tu montres décrit justement la création du secret contenant le `hdfs-site.xml`.

Je te conseille d'éviter une ironie trop visible dans le mail : le simple fait de mentionner que le diagnostic vient d'un `kubectl describe pod` suffit à faire passer le message.

### Réponse proposée

**Subject: RE: RITM7578385 | QUAL/UAT | Spark job failing to start**

Hi Priya, Srinath,

I have checked the reported issue.

The root cause is clearly reported by Kubernetes and can be identified directly from a simple `kubectl describe pod` on the Spark driver:

> `FailedMount: MountVolume.SetUp failed for volume "hadoop-conf": secret "vm-hadoop-conf" not found`

The SparkApplication is successfully created. The driver remains in `ContainerCreating` because Kubernetes cannot mount the required `hadoop-conf` volume, as the referenced Secret `vm-hadoop-conf` is missing from the namespace.

This configuration is also covered in the SparkaaS documentation, including the creation of the Secret containing the required `hdfs-site.xml` configuration.

Could you please confirm whether your team has access to the Spark pods and namespace? If yes, checking the driver pod with `kubectl describe pod` should be the first diagnostic step for this type of startup issue, as Kubernetes directly provides the blocking reason in the Events section.

Please verify/create the required Secret according to the documentation and retry the Spark application.

At this stage, there is no indication of an Airflow, Spark platform or Build issue requiring N2/N3 escalation.

Regards,
Djamel
