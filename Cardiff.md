Les deux captures semblent montrer **le même problème vu sous deux angles : l’application DataHub n’arrive plus à joindre le service d’ingestion, et Illumio bloque les flux réseau associés.**

### 1. Côté application

L'erreur principale est répétée plusieurs fois :

```text
HTTPSConnectionPool(
 host='datafabric-ingestion-notif-c01.staging.echonet',
 port=443
)
...
ConnectTimeoutError
Connection to datafabric-ingestion-notif-c01.staging.echonet timed out
```

Donc :

* destination : `datafabric-ingestion-notif-c01.staging.echonet`
* port : **443 / HTTPS**
* plusieurs API sont impactées :

  * `/process/api/v1/mediation/zip-status`
  * `/process/api/v1/toolbox/files/rename`
  * `/process/api/v1/mediation/zip-metadata`
  * `/process/api/v1/ingestion/notif-async`
* ce n'est **pas une erreur applicative fonctionnelle** à première vue.
* l'application essaie de se connecter mais **la connexion TCP vers le serveur distant expire**.

### 2. Côté Illumio

La deuxième capture montre beaucoup de :

**`Blocked`**

avec notamment :

```text
action = Blocked
protocol = TCP
destination port = 80
source IP = 198.18.130.x / 198.18.131.x
destination IP = 169.254.16.9
```

et les labels :

```text
src environment = E_PROD
src location    = L_EMEA_T2_BNPP_DMZR...
src application = A_AP63215-ASS-DATA-FABRIC_...
src role        = R_RESTRICTED_A_KUBE_OTHER...
```

Donc Illumio voit bien des flux provenant de **Data Fabric / Kubernetes en PROD** et les bloque.

### 3. Le point important

Il faut toutefois faire attention : **la capture Illumio montrée n'est pas directement la preuve du timeout vers `datafabric-ingestion-notif-c01.staging.echonet:443`.**

Pourquoi ?

Dans l'erreur applicative :

```text
destination = datafabric-ingestion-notif-c01.staging.echonet
port = 443
```

Alors que dans la capture Illumio :

```text
destination port = 80
destination IP = 169.254.16.9
```

Il faut donc vérifier qu'il s'agit bien **du même flux après résolution DNS / éventuel proxy / load balancer**, et pas simplement d'un autre flux bloqué généré par la même application.

### Ce que je vérifierais en priorité

Depuis le pod concerné :

```bash
nslookup datafabric-ingestion-notif-c01.staging.echonet
```

puis :

```bash
curl -vk --connect-timeout 5 https://datafabric-ingestion-notif-c01.staging.echonet:443
```

Et surtout récupérer l'IP :

```bash
getent hosts datafabric-ingestion-notif-c01.staging.echonet
```

Ensuite, dans Illumio, chercher **cette IP destination + port 443**.

Si tu trouves :

```text
SRC = pod DataHub
DST = IP de datafabric-ingestion-notif-c01
PORT = 443
ACTION = Blocked
```

alors tu as pratiquement la corrélation :

**Enforcement Illumio → flux HTTPS bloqué → timeout applicatif.**

### Pour ton incident

Je formulerais la conclusion provisoire ainsi :

> **The application is unable to connect to `datafabric-ingestion-notif-c01.staging.echonet` on HTTPS/443. The connection times out. Illumio shows blocked traffic from the Data Fabric/Kubernetes environment. We are checking the destination IP and port 443 to confirm that the blocked Illumio flow corresponds to the application timeout.**

C'est la bonne approche : **ne pas encore dire que l'Illumio est définitivement la cause racine tant que le flux `destination IP:443` n'est pas retrouvé dans les logs Illumio.**
