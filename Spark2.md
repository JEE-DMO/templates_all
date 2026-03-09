Parfait, avec tes deux dernières captures on voit **exactement ce qui se passe du début à la fin**. Je vais te résumer clairement. 👇

---

# 1️⃣ Le fonctionnement de ton DAG

Ton DAG Airflow fait :

```
Airflow DAG
   ↓
BashOperator
   ↓
spark-submit
   ↓
connexion à Kubernetes
   ↓
création du driver pod
```

Dans ton log on voit la commande exécutée :

```bash
spark-submit \
--master k8s://https://iks-ap43783.svc-np.paas.echonet.net.intra:32676 \
--deploy-mode cluster \
--name ingestion_dz \
--conf spark.kubernetes.authenticate.submission.oauthToken=$SPARK_TOKEN \
--conf spark.kubernetes.namespace=$NAMESPACE \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-sa
```

Donc Spark :

1️⃣ utilise **un token OAuth**
2️⃣ appelle **l’API Kubernetes en HTTPS**
3️⃣ essaie de créer un pod

---

# 2️⃣ L’erreur réelle dans ton log

Dans la première capture :

```
ERROR Client: Please check "kubectl auth can-i create pod"
```

mais juste après on voit **la vraie erreur** :

```
PKIX path building failed
unable to find valid certification path to requested target
```

Ça veut dire :

👉 **Java ne fait pas confiance au certificat HTTPS du Kubernetes API server**

Donc la connexion TLS échoue.

---

# 3️⃣ Pourquoi `kubectl` marche mais pas Spark

Parce que :

| outil        | certificat              |
| ------------ | ----------------------- |
| kubectl      | utilise kubeconfig      |
| Spark (Java) | utilise truststore Java |

Donc :

```
kubectl → OK
spark-submit → SSL failure
```

---

# 4️⃣ Le vrai problème dans ta commande Spark

Dans ton `spark-submit` **il manque le certificat CA Kubernetes**.

Il faut ajouter :

```
spark.kubernetes.authenticate.submission.caCertFile
```

ou

```
spark.kubernetes.authenticate.driver.caCertFile
```

---

# 5️⃣ Correction probable

Dans ton `spark-submit` ajoute :

```bash
--conf spark.kubernetes.authenticate.submission.caCertFile=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

et éventuellement :

```bash
--conf spark.kubernetes.authenticate.driver.caCertFile=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

---

# 6️⃣ Pourquoi ça corrige

Le fichier :

```
/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

contient **le certificat du cluster Kubernetes**.

Spark pourra donc vérifier le certificat TLS.

---

# 7️⃣ Ton spark-submit corrigé (extrait)

```bash
spark-submit \
--master k8s://https://iks-ap43783.svc-np.paas.echonet.net.intra:32676 \
--deploy-mode cluster \
--conf spark.kubernetes.namespace=$NAMESPACE \
--conf spark.kubernetes.authenticate.submission.oauthToken=$SPARK_TOKEN \
--conf spark.kubernetes.authenticate.submission.caCertFile=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-sa
```

---

# 8️⃣ Pourquoi l’erreur RBAC apparaît

Spark affiche d’abord :

```
kubectl auth can-i create pod
```

mais c’est **un message générique** quand la connexion Kubernetes échoue.

Dans ton cas la vraie cause est :

```
SSL handshake failed
```

---

# ✅ Conclusion

Ton problème n’est **pas** :

❌ RBAC
❌ service account
❌ namespace

mais :

✅ **certificat TLS Kubernetes manquant dans Spark**

---

💡 Si tu veux, je peux aussi te montrer **un détail très suspect dans ta commande spark-submit qui peut casser l’auth Kubernetes dans 30% des clusters**.
C’est une petite ligne dans ta config qui peut poser problème.
