Tu as raison de souligner ça — et c’est **exactement le type d’argument qu’un utilisateur technique va utiliser pour challenger la RCA**.
Si la rotation est fréquente **mais que le problème n’arrive pas à chaque rotation**, alors la root cause n’est **probablement pas juste “rotation = restart nécessaire”**. Il faut être plus précis.

Voici l’explication la plus cohérente avec ton architecture.

---

# Ce qui se passe probablement

Dans ton stack :

* External Secrets Operator met à jour les **Secrets Kubernetes**
* le webserver **Airflow** consomme ces secrets comme **variables d’environnement**
* Airflow **ne recharge pas dynamiquement les env vars**

Normalement, quand un secret change :

1. le secret Kubernetes est mis à jour
2. un mécanisme (ex: reloader) redémarre les pods
3. le webserver recharge la config

Mais si **le pod ne redémarre pas**, il garde l’ancienne config en mémoire.

---

# Pourquoi ça n’arrive pas à chaque rotation

Plusieurs raisons possibles (et très courantes) :

### 1️⃣ La rotation ne change pas réellement la valeur

Certaines rotations **renouvellent le secret côté backend mais gardent la même valeur**.

Donc :

```
secret backend rotated
→ valeur identique
→ Kubernetes Secret identique
→ pas de restart
→ pas de problème
```

---

### 2️⃣ Le secret n’est pas celui utilisé par le webserver

Parfois plusieurs secrets existent :

```
keycloak-admin-secret
oidc-client-secret
```

Si la rotation concerne **un autre secret**, Airflow n’est pas impacté.

---

### 3️⃣ Le mécanisme de restart automatique ne se déclenche pas toujours

Si tu utilises un outil comme :

* secret reloader
* annotations Helm
* ArgoCD sync

il peut arriver que :

```
secret updated
→ checksum du pod template inchangé
→ pod non redémarré
```

---

### 4️⃣ Le webserver avait déjà été redémarré récemment

Si le pod a redémarré pour une autre raison :

* déploiement
* node drain
* scaling

alors il utilise déjà la **nouvelle config**.

---

# La RCA la plus honnête à communiquer

Tu peux dire :

> L’incident provient d’une désynchronisation ponctuelle entre la configuration d’authentification OIDC utilisée en mémoire par le service webserver Airflow et la valeur du secret Kubernetes mis à jour lors de la rotation. Airflow ne recharge pas dynamiquement ces paramètres ; ils sont chargés uniquement au démarrage du service. Dans ce cas précis, le webserver continuait d’utiliser l’ancienne valeur du secret, ce qui a entraîné le refus d’authentification. Le redémarrage du service a permis de recharger la configuration et de rétablir l’accès.

Puis ajouter :

> Ce type de situation ne se produit pas systématiquement lors des rotations car il dépend du moment où les pods sont redémarrés par les mécanismes de déploiement ou d’orchestration.

---

# Pourquoi cette RCA est solide

Elle explique :

* pourquoi **ça arrive parfois**
* pourquoi **le restart corrige**
* pourquoi **la rotation seule ne suffit pas**

sans inventer de cause.

---

💡 Si tu veux, je peux aussi te montrer **le vrai indicateur dans Kubernetes qui permet de prouver à 100% que c’est une désynchronisation secret / pod** (et ça renforce énormément une RCA auprès des utilisateurs).
