OK 👍 — avec cette capture on voit **exactement pourquoi ça casse**.

👉 Tu lances Spark **en mode client depuis CodeHub**, mais ta config Kubernetes n’expose pas correctement le **driver** aux executors.

Et ça correspond parfaitement à ton erreur précédente :

```
UnknownHostException
Failed to connect ... :4401
```

---

# 🎯 Le vrai problème

Tu fais :

```python
.master("k8s://https://iks-ap43783...")
```

➡️ **mode client implicite** (puisque lancé depuis notebook CodeHub).

Donc :

✅ Driver = dans le notebook CodeHub
✅ Executors = pods Kubernetes

⚠️ MAIS :

> les executors doivent pouvoir joindre le driver via un hostname routable.

Actuellement → **ils ne peuvent pas résoudre l’adresse du driver**.

---

# 🧠 Pourquoi ça ne marche pas

En mode **client**, Spark fait :

```
Executor pod  --->  Driver (ton notebook)
```

Mais ton driver :

* tourne hors du cluster K8s
* n’a pas d’adresse DNS interne Kubernetes
* n’expose pas spark.driver.host

Donc Kubernetes essaie de joindre un hostname invalide → 💥 DNS failure.

---

# 🔥 Indice dans tes logs

Avant tu avais :

```
UnknownHostException: codemub-xxxxx
```

👉 C’est le hostname auto-détecté du notebook.

Kubernetes ne connaît PAS ce hostname.

---

# ✅ Solution (2 options)

## ⭐ OPTION 1 — RECOMMANDÉE (90% des cas)

👉 Passe en **cluster mode**.

C’est la bonne pratique avec Spark on Kubernetes.

### Ajoute :

```python
.config("spark.submit.deployMode", "cluster")
```

OU via spark-submit :

```bash
--deploy-mode cluster
```

---

### Ce que ça change

```
AVANT
Notebook (driver) ❌
        ↑
Executors (K8s)

APRÈS
Driver pod (K8s) ✅
        ↑
Executors (K8s)
```

➡️ Tout reste dans Kubernetes → DNS OK.

---

## ⭐ OPTION 2 — garder client mode (plus compliqué)

Tu dois définir explicitement :

```python
.config("spark.driver.host", "<IP accessible depuis K8s>")
.config("spark.driver.bindAddress", "0.0.0.0")
.config("spark.driver.port", "7078")
```

ET :

* ouvrir les ports réseau
* rendre CodeHub accessible depuis le cluster
* gérer firewall / NAT

👉 honnêtement : **douleur garantie** 😄

---

# ✅ Correction minimale de ton code

Ajoute juste :

```python
spark = (
    SparkSession.builder
    .appName(name)
    .master("k8s://https://iks-ap43783.svc-np.paas.echonet.net.intra:30633")
    .config("spark.submit.deployMode", "cluster")   # ⭐ AJOUT
    .config("spark.kubernetes.namespace", KUBE_NS)
    ...
    .getOrCreate()
)
```

---

# ⚠️ Très important (souvent oublié)

En cluster mode, ton image doit contenir :

* ton code Python
* dépendances
* libs

Sinon driver pod ne trouvera pas ton notebook/script.

---

# 🧩 Pourquoi ça marchait pas (résumé ultra court)

| Élément   | Situation            |
| --------- | -------------------- |
| Mode      | client               |
| Driver    | CodeHub              |
| Executors | Kubernetes           |
| DNS       | impossible           |
| Résultat  | UnknownHostException |

---

# 🚀 Ce que je te conseille (niveau Data Engineer)

👉 **Spark + Kubernetes + Notebook = toujours cluster mode**.

Client mode est quasi uniquement pour debug local.

---

Si tu veux, je peux aussi te montrer **la config production propre** utilisée en entreprise (avec driver service auto + retry + logs propres).
Dis juste 👍.
