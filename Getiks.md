Parfait. On va construire une **V2 vraiment propre et puissante**, typique d’un outil DevOps interne.
Objectifs :

* 🔎 **Recherche simple** : `dh ap43970`
* ⚡ **Recherche rapide (fuzzy)** dans tout le mapping
* 🎨 **table colorée**
* 🔢 **menu interactif**
* ☸ **connexion automatique au cluster**
* 📦 **lancement direct de `k9s` sur le namespace**
* 🌐 **URL cliquable**
* 📁 **mapping dans le même dossier**
* 🧠 **script propre et robuste**

---

# 1️⃣ Structure

Dans un dossier :

```
datahub-cli/
 ├─ dh
 └─ dh_map.csv
```

---

# 2️⃣ Script `dh` (version propre)

```bash
#!/usr/bin/env bash

MAP="$(dirname "$0")/dh_map.csv"

RED='\033[1;31m'
GREEN='\033[1;32m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f "$MAP" ]; then
  echo "Mapping file not found"
  exit 1
fi

QUERY="$*"

if [ -z "$QUERY" ]; then
  echo -e "${YELLOW}Usage:${NC} dh <search>"
  exit
fi

RESULTS=$(grep -i "$QUERY" "$MAP")

COUNT=$(echo "$RESULTS" | grep -c .)

if [ "$COUNT" -eq 0 ]; then
  echo -e "${RED}No instance found${NC}"
  exit
fi

print_instance() {

IFS=',' read -r bl apcd env ruid ns ver url ibm iks <<< "$1"

echo
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN} DataHub Instance${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

printf "${CYAN}BL         ${NC}: %s\n" "$bl"
printf "${CYAN}APCD       ${NC}: %s\n" "$apcd"
printf "${CYAN}ENV        ${NC}: %s\n" "$env"
printf "${CYAN}Namespace  ${NC}: %s\n" "$ns"
printf "${CYAN}Version    ${NC}: %s\n" "$ver"
printf "${CYAN}IKS        ${NC}: %s\n" "$iks"

echo
echo -e "${YELLOW}URL:${NC} $url"

echo
echo -e "${GREEN}Connecting to cluster...${NC}"

iks "$iks"

echo -e "${GREEN}Opening k9s...${NC}"

k9s -n "$ns"

}

if [ "$COUNT" -eq 1 ]; then

print_instance "$RESULTS"

exit

fi

echo
echo -e "${GREEN}Instances found:${NC}"
echo

i=1
declare -a LINES

printf "${CYAN}%-4s %-6s %-10s %-6s %-35s\n${NC}" "ID" "BL" "APCD" "ENV" "NAMESPACE"

while read -r line; do

LINES[$i]="$line"

IFS=',' read -r bl apcd env ruid ns ver url ibm iks <<< "$line"

printf "${YELLOW}%-4s${NC} %-6s %-10s %-6s %-35s\n" "$i" "$bl" "$apcd" "$env" "$ns"

((i++))

done <<< "$RESULTS"

echo
read -p "Choose instance > " CHOICE

print_instance "${LINES[$CHOICE]}"
```

---

# 3️⃣ Exemple mapping `dh_map.csv`

Export direct depuis ton Excel.

```csv
BL,APCD,ENV,RUID,NS,VER,URL,IBM,IKS
dhpf,ap43970,prod,43505881,astronomer-ap43970-prod,3.4.1,https://astronomer-ap43970-prod.data.cloud.net.intra,xxx,iks-ap43970-hprd
dhpf,ap43970,prod,92730182,spark-ap43970-prod,4.1.5,https://sparku-ap43970-prod.data.cloud.net.intra,xxx,iks-ap43970-hprd
bcef,ap43783,dev,2103030,spark-ap43783-dev,4.1.5,https://sparku-ap43783-dev.data.cloud.net.intra,xxx,iks-ap43783-hprd
```

---

# 4️⃣ Installation

```bash
chmod +x dh
sudo mv dh /usr/local/bin
```

ou dans ton repo CodeHub :

```bash
export PATH=$PATH:/path/datahub-cli
```

---

# 5️⃣ Utilisation

### Recherche simple

```
dh ap43970
```

ou

```
dh 43970
```

ou

```
dh spark
```

---

# 6️⃣ Exemple terminal

```
Instances found:

ID   BL     APCD       ENV    NAMESPACE
1    dhpf   ap43970    prod   spark-ap43970-prod
2    dhpf   ap43970    prod   astronomer-ap43970-prod

Choose instance >
```

Puis :

```
Connecting to cluster...
iks iks-ap43970-hprd

Opening k9s...
```

---

# 7️⃣ Résultat

Tu arrives **directement dans k9s sur le bon namespace**.

```
k9s -n spark-ap43970-prod
```

---

# 8️⃣ Améliorations possibles (V3)

Je peux te faire une **version encore plus avancée (très utilisée en plateforme data)** :

* 🔎 **recherche fuzzy intelligente**
* ⚡ **instant search**
* 🎨 **UI terminal style kubectl**
* ⌨ **autocomplete**
* 🌐 **open URL navigateur**
* ☸ **kubectl context automatique**
* 📦 **liste pods**
* 📊 **affichage spark / astro séparé**

Exemple :

```
dh ap43970
```

```
╭────────────────────────────────────╮
│ DataHub Explorer                   │
├────────────────────────────────────┤
│ 1 spark       prod   ap43970       │
│ 2 astronomer  prod   ap43970       │
╰────────────────────────────────────╯
```

et ça devient **un outil plateforme officiel**.

Si tu veux, je peux aussi te faire une **V3 ultra stylée (~200 lignes) que ton équipe va adorer**.
