Oui. Remplace le principe par :

```bash
dh update
dh airflow prod A101737
dh spark hprd qual client-x
dh prod A101737
dh A101737
```

## Logique

Tout ce qui est après `dh` devient une liste de mots à matcher sur la ligne CSV complète.

Règle :

```text
dh xxx yyy zzz
=> retourne les lignes qui contiennent xxx ET yyy ET zzz
```

Sans option, sans `search`.

## Remplacement dans le script

Remplace le `case` final par :

```bash
main() {
  local cmd="${1:-}"

  case "$cmd" in
    update)
      shift
      cmd_update "$@"
      ;;
    show)
      shift
      cmd_show "$@"
      ;;
    connect)
      shift
      cmd_connect "$@"
      ;;
    ""|-h|--help)
      usage
      ;;
    *)
      cmd_match "$@"
      ;;
  esac
}

main "$@"
```

Ajoute cette fonction :

```bash
cmd_match() {
  [[ -f "$MAPPING_FILE" ]] || {
    echo "Mapping not found. Run: dh update"
    exit 1
  }

  [[ $# -gt 0 ]] || {
    usage
    exit 1
  }

  awk -F',' -v terms="$*" '
    BEGIN {
      n = split(tolower(terms), t, " ")
    }

    NR == 1 { next }

    {
      line = tolower($0)

      for (i = 1; i <= n; i++) {
        if (line !~ t[i]) {
          next
        }
      }

      id=$1
      service=$2
      client=$3
      apcode=$4
      envtype=$5
      env=$6
      namespace=$7
      instance=$8
      iks_version=$10
      url=$11
      iks_name=$12
      ibm_account=$13

      gsub(/"/, "", id)
      gsub(/"/, "", service)
      gsub(/"/, "", client)
      gsub(/"/, "", apcode)
      gsub(/"/, "", envtype)
      gsub(/"/, "", env)
      gsub(/"/, "", namespace)
      gsub(/"/, "", instance)
      gsub(/"/, "", iks_version)
      gsub(/"/, "", url)
      gsub(/"/, "", iks_name)
      gsub(/"/, "", ibm_account)

      print id "|" service "|" client "|" apcode "|" envtype "/" env "|" namespace "|" iks_name "|" ibm_account "|" iks_version
    }
  ' "$MAPPING_FILE" | column -t -s '|'
}
```

Et simplifie le `usage` :

```bash
usage() {
  cat <<EOF
Usage:
  dh update
  dh <text> [text...]
  dh show <id>
  dh connect <id>

Examples:
  dh airflow prod A101737
  dh spark hprd qual
  dh starburst client-x prod
  dh A101737
EOF
}
```

## Résultat attendu

```bash
dh airflow prod A101737
```

Retourne uniquement les lignes contenant les trois chaînes :

```text
airflow
prod
A101737
```

Même logique pour :

```bash
dh spark qual risk
dh starburst pprd A999999
dh astronomer a101737
```
