Je lis dans tes captures exactement un cas “certs manquants dans l’image/pod Spark” :

* **Erreur** (log) : `requests` → `SSLError` → `CERTIFICATE_VERIFY_FAILED` → **`self signed certificate in certificate chain`** sur un endpoint **OIDC token** (`.../protocol/openid-connect/token`)
* **Conclusion** : **dans le cluster Spark (driver/executor pods)**, la **chaîne de confiance (CA BNP / intermédiaires)** n’est pas présente (ou pas pointée par Python).
* **Pourquoi ça marche sur CodeHub** : l’environnement CodeHub a très probablement déjà le **bundle CA corporate** (ou une conf `REQUESTS_CA_BUNDLE/SSL_CERT_FILE`) → la vérification TLS passe.

---

## Cause racine (simple)

Ce n’est **pas** “le serveur qui ne fait pas confiance au pod”.
En TLS classique : **c’est le client (ton pod Spark) qui doit faire confiance au serveur**. Sofiane a raison dans la discussion.

Ici, ton pod Spark **ne connaît pas** la CA qui a signé le cert du serveur (ou il voit une chaîne incomplète), donc `requests` refuse.

---

## Ce que tu dois vérifier tout de suite (2 minutes, sans blabla)

### 1) Depuis le **driver pod Spark** (mode cluster)

```bash
# 1) Identifier le pod driver
kubectl -n <ns_spark> get pods | grep driver

# 2) Vérifier le certificat présenté par le serveur
kubectl -n <ns_spark> exec -it <pod-driver> -- sh -lc '
  apk add --no-cache openssl 2>/dev/null || true;
  openssl s_client -connect <host>:443 -servername <host> -showcerts </dev/null | sed -n "1,120p"
'
```

Tu verras souvent : chaîne incomplète / CA inconnue / self-signed in chain.

### 2) Vérifier côté Python (dans le pod)

```bash
kubectl -n <ns_spark> exec -it <pod-driver> -- sh -lc '
python3 - <<PY
import os, certifi
print("REQUESTS_CA_BUNDLE=", os.getenv("REQUESTS_CA_BUNDLE"))
print("SSL_CERT_FILE=", os.getenv("SSL_CERT_FILE"))
print("certifi.where()=", certifi.where())
PY
'
```

---

## Fix rapide (workaround) si tu veux débloquer le user **maintenant**

### Option A — monter un bundle CA et le forcer pour `requests`

1. Tu récupères le **CA bundle** (root + intermédiaires BNP nécessaires) au format PEM : `bnpp-ca-chain.pem`
2. Tu le mets dans un **ConfigMap** (ou Secret si politique interne) et tu le montes dans le pod Spark.
3. Tu forces Python via env vars **driver + executors** :

**spark-submit / Spark conf :**

```bash
--conf spark.kubernetes.driverEnv.REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/bnpp-ca-chain.pem \
--conf spark.kubernetes.executorEnv.REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/bnpp-ca-chain.pem \
--conf spark.kubernetes.driverEnv.SSL_CERT_FILE=/etc/pki/ca-trust/bnpp-ca-chain.pem \
--conf spark.kubernetes.executorEnv.SSL_CERT_FILE=/etc/pki/ca-trust/bnpp-ca-chain.pem
```

Et côté code (si tu veux bétonner) :

```python
import os, requests
ca = os.getenv("REQUESTS_CA_BUNDLE", "/etc/pki/ca-trust/bnpp-ca-chain.pem")
r = requests.post(url, data=data, verify=ca, timeout=30)
```

> Point critique : **si l’appel API est fait dans des tasks distribuées** (executors), il faut aussi les env vars **executorEnv** (sinon driver OK mais executors KO).

### Option B — (temporaire, à éviter) `verify=False`

Ça marche mais **c’est une régression sécu**. À utiliser uniquement pour prouver le diagnostic (POC), pas pour prod.

---

## Fix “propre” à demander à l’équipe Build (Sofiane) pour Sparkaas

Le bon correctif plateforme, c’est **ajouter les CA BNP** dans l’image Spark **ou** fournir un mécanisme standard d’injection :

1. **Dans l’image de base Spark** : installer le bundle CA corporate dans le trust OS

   * Debian/Ubuntu : `/usr/local/share/ca-certificates/*.crt` + `update-ca-certificates`
   * RHEL-like : `update-ca-trust`
2. Ou **InitContainer** qui copie les CA puis met à jour le truststore, partagé via volume.
3. Documenter un “hook” type : `spark-defaults` / `values.yaml` / `configmap certs` pour que le client puisse déposer son CA chain.

---

## Le message “utile” que tu peux mettre dans le ticket (clair + actionnable)

Tu peux coller ça (en anglais) :

> We are hitting `SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED (self signed certificate in certificate chain)` only when running the Spark job in **cluster mode** (driver/executors pods). Same code works from CodeHub, which suggests the Spark image/pods are missing BNP root/intermediate CA chain (or Python requests is not pointing to it).
> **Request:** please provide a supported way to inject BNP CA bundle into Spark driver/executor pods (image trust store or mounted CA bundle + env `REQUESTS_CA_BUNDLE/SSL_CERT_FILE`).
> We can validate by running `openssl s_client -showcerts -connect <host>:443 -servername <host>` from the Spark driver pod.

---

## En résumé (diagnostic + next step)

* ✅ Diagnostic : **truststore CA manquant dans les pods Spark** (driver/executors) → `requests` refuse le TLS.
* ✅ Next step le plus efficace : **monter la CA chain en PEM + `REQUESTS_CA_BUNDLE` sur driver+executors**.
* ✅ Fix long-terme : **Build équipe** met les CA BNP dans l’image / mécanisme officiel d’injection.

Si tu me donnes juste **le host** (ou au moins le pattern, ex `wmmiam...` / `bnpp...`) et **comment le job est lancé** (spark-submit direct, Airflow, template Sparkaas), je te fournis **le bloc exact** `--conf` + manifest ConfigMap/volumeMount correspondant à votre Sparkaas.
