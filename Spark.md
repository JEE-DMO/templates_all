Pour diagnostiquer ton problème, tu dois vérifier **3 choses sur le cluster Kubernetes**.
Les commandes sont simples et permettent de confirmer rapidement si c’est bien un problème **RBAC/service account**.

---

# 1️⃣ Vérifier si le service account existe

Dans ton `spark-submit` on voit :

```
spark.kubernetes.authenticate.driver.serviceAccountName=spark-sa
```

Donc vérifie qu’il existe dans le namespace utilisé.

```bash
kubectl get sa -n <namespace>
```

Tu dois voir :

```
spark-sa
```

Sinon Spark utilise un service account qui **n’existe pas**.

---

# 2️⃣ Vérifier les permissions du service account

C’est **la vérification la plus importante**.

```bash
kubectl auth can-i create pods \
--as system:serviceaccount:<namespace>:spark-sa \
-n <namespace>
```

Résultat attendu :

```
yes
```

Si tu as :

```
no
```

➡️ c’est **exactement ton problème** : le service account n’a pas les droits.

---

# 3️⃣ Vérifier les RoleBinding

Pour voir si `spark-sa` a des permissions :

```bash
kubectl get rolebinding -n <namespace>
```

Puis :

```bash
kubectl describe rolebinding <rolebinding-name> -n <namespace>
```

Regarde si tu vois :

```
ServiceAccount: spark-sa
```

---

# 4️⃣ Vérifier si Spark arrive à créer des pods

Juste pour confirmer :

```bash
kubectl get pods -n <namespace>
```

Normalement tu devrais voir des pods comme :

```
spark-xxxxx-driver
spark-xxxxx-exec-1
```

Dans ton cas **il n’y en aura pas** car la création est refusée.

---

# 📊 Résumé rapide des commandes

```bash
# vérifier le service account
kubectl get sa -n <namespace>

# vérifier les permissions
kubectl auth can-i create pods --as system:serviceaccount:<namespace>:spark-sa -n <namespace>

# vérifier les roles
kubectl get rolebinding -n <namespace>

# vérifier les pods spark
kubectl get pods -n <namespace>
```

---

💡 **Très probable dans ton cas :**

```
kubectl auth can-i create pods → no
```

et il faudra créer un **RoleBinding pour spark-sa**.

---

✅ Si tu veux, envoie-moi aussi **la commande spark-submit complète** (celle qu’on voit dans ton log) et je peux te dire **exactement dans quel namespace Spark essaie de créer le pod**, parce que je vois déjà un détail suspect dans ton log.
