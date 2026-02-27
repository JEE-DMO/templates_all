OK 👍
On va faire un **script shell générique** qui :

✅ lit un **CSV dans le même dossier que le script**
✅ permet de filtrer par :

* `BL`
* `APCD`
* `IKS`
* `ENV`
* combinaisons :

  * BL + APCD
  * BL + ENV
  * APCD + ENV
  * etc.
    ✅ affiche les lignes correspondantes

On va utiliser **awk** (rapide, natif Linux, parfait pour CSV simple).

---

# ✅ 1. Structure attendue

On suppose un CSV comme ton image :

```csv
BL,APCD,ENV,RUID,VER,IBM,IKS
bcf,ap80414,dev,xxxx,3.5.2,aaaa,iks-xxx
...
```

Nom du fichier (modifiable) :

```
mapping.csv
```

Script :

```
filter.sh
```

dans le **même dossier**.

---

# ✅ 2. Script shell complet

Crée `filter.sh` :

```bash
#!/usr/bin/env bash

CSV_FILE="$(dirname "$0")/mapping.csv"

if [ ! -f "$CSV_FILE" ]; then
    echo "❌ CSV introuvable: $CSV_FILE"
    exit 1
fi

usage() {
    echo "Usage:"
    echo "  $0 [-b BL] [-a APCD] [-e ENV] [-i IKS]"
    echo
    echo "Exemples:"
    echo "  $0 -b bcf"
    echo "  $0 -a ap80414"
    echo "  $0 -b bcf -e dev"
    echo "  $0 -b bcf -a ap80414"
    echo "  $0 -i iks-ap80414-hprd"
    exit 1
}

# Variables filtres
BL=""
APCD=""
ENV=""
IKS=""

# Lecture arguments
while getopts "b:a:e:i:h" opt; do
  case $opt in
    b) BL="$OPTARG" ;;
    a) APCD="$OPTARG" ;;
    e) ENV="$OPTARG" ;;
    i) IKS="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

awk -F',' -v bl="$BL" -v apcd="$APCD" -v env="$ENV" -v iks="$IKS" '
BEGIN { IGNORECASE=1 }

NR==1 {
    print $0
    next
}

{
    cond=1

    if (bl   != "" && $1 != bl)   cond=0
    if (apcd != "" && $2 != apcd) cond=0
    if (env  != "" && $3 != env)  cond=0
    if (iks  != "" && $7 !~ iks)  cond=0

    if (cond) print $0
}
' "$CSV_FILE"
```

---

# ✅ 3. Rendre exécutable

```bash
chmod +x filter.sh
```

---

# ✅ 4. Utilisation

## 🔹 Filtrer par BL

```bash
./filter.sh -b bcf
```

---

## 🔹 Filtrer par APCD

```bash
./filter.sh -a ap80414
```

---

## 🔹 BL + ENV

```bash
./filter.sh -b bcf -e dev
```

---

## 🔹 BL + APCD

```bash
./filter.sh -b bcf -a ap80414
```

---

## 🔹 APCD + ENV

```bash
./filter.sh -a ap80414 -e qual
```

---

## 🔹 Filtrer par IKS (match partiel)

```bash
./filter.sh -i ap80414
```

---

# ✅ 5. Ce que fait le script (important)

* garde l’en-tête CSV
* filtres combinables librement
* insensitive à la casse (`DEV = dev`)
* aucun filtre → affiche tout

---

# ⭐ Version PRO (optionnelle)

Je peux aussi te faire une version qui :

✅ accepte CSV avec séparateur `;` ou `,` automatiquement
✅ sortie en tableau aligné (`column -t`)
✅ autocomplétion bash
✅ recherche fuzzy (comme kubectl)
✅ mode interactif (`fzf`)
✅ export résultat → nouveau CSV

👉 Dis-moi si tu veux la **version data engineer clean** 😄.
