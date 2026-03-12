Voici **deux descriptions prêtes à être utilisées dans des demandes SNOW**, une pour **HPRD** et une pour **PROD** (avec la partie Illumio). Elles sont **factuelles, basées sur tes tests et ton analyse**.

---

**Titre :** Vérification de la résolution DNS pour accès Oracle SCAN depuis le cluster (HPRD)

Dans le cadre d’un incident en cours, nous investiguons un problème de connexion des jobs Spark vers une base Oracle RAC.

Les clients doivent se connecter via le hostname SCAN `exa08-scan.ctlm.de` (et non via une adresse IP), car ce DNS retourne plusieurs IP utilisées par Oracle RAC pour le load balancing.

Tests effectués :

* Depuis une machine du réseau corporate, la résolution DNS fonctionne correctement et retourne plusieurs IP.

* Exemple :

  nslookup exa08-scan.ctlm.de
  → 55.32.163.20
  → 55.32.163.19
  → 55.32.163.21

* Depuis un pod Kubernetes du cluster, la résolution échoue :

  nslookup exa08-scan.ctlm.de
  Server: 198.18.0.10
  → NXDOMAIN

Cela indique que le DNS utilisé par le cluster ne résout pas le domaine `ctlm.de`.

Demande :
Pouvez-vous vérifier la configuration DNS du cluster (CoreDNS / forwarding DNS) afin de confirmer que le domaine `ctlm.de` est correctement résolu depuis les pods Kubernetes ?

Preuve jointe : capture des tests nslookup depuis le pod et depuis le réseau corporate.

---

**Titre :** Vérification DNS + ouverture flux Illumio pour accès Oracle SCAN depuis le cluster (PROD)

Dans le cadre d’un incident en cours, nous investiguons un problème de connexion des jobs Spark vers une base Oracle RAC en production.

Les applications doivent se connecter via le hostname SCAN `exa09-scan.ctlm.de` (et non via une adresse IP), car ce DNS retourne plusieurs adresses IP utilisées par Oracle RAC pour le load balancing.

Tests effectués :

* Depuis une machine du réseau corporate, la résolution DNS fonctionne correctement et retourne plusieurs IP :

  nslookup exa09-scan.ctlm.de
  → 55.32.163.26
  → 55.32.163.28
  → 55.32.163.27

* Depuis un pod Kubernetes du cluster, la résolution DNS échoue (NXDOMAIN) via le DNS utilisé par le cluster.

Analyse :
Le cluster ne semble pas résoudre le domaine `ctlm.de`, ce qui empêche les jobs d’utiliser le hostname SCAN Oracle.

Demandes :

1. Vérifier la configuration DNS du cluster afin de confirmer que le domaine `ctlm.de` est correctement résolu depuis les pods Kubernetes.
2. Vérifier / ouvrir les flux réseau Illumio nécessaires entre le cluster et les IP Oracle SCAN suivantes sur le port Oracle (1521) :

   55.32.163.26
   55.32.163.28
   55.32.163.27

Preuves jointes : captures des tests nslookup depuis le réseau corporate et depuis un pod Kubernetes.

---

Si tu veux, je peux aussi te faire **une version encore plus "SNOW style" (plus courte, très standardisée)** que les équipes infra préfèrent souvent.
