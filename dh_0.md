Voici une base propre pour ton outil `dh`.

## Design cible

```bash
dh update
dh search --apcode A123456 --service airflow --env prod
dh search --client myclient --envtype hprd
dh show 1
dh connect 1
```

## CSV normalisé

Fichier local :

```bash
~/.dh/mapping.csv
```

Colonnes communes :

```csv
id,service,client,apcode,envtype,env,namespace,instance_name,version,iks_version,url,iks_name,ibm_account,region,cp_source,updated_at
```

Services :

```text
spark      -> SparkUI / History URL
airflow    -> Airflow Webserver URL
starburst  -> Starburst portal/coordinator URL
```

---

## Script `dh`

À mettre dans `/usr/local/bin/dh` ou `~/bin/dh`.

```bash
#!/usr/bin/env bash
set -euo pipefail

DH_HOME="${DH_HOME:-$HOME/.dh}"
MAPPING_FILE="$DH_HOME/mapping.csv"
CACHE_DIR="$DH_HOME/cache"

mkdir -p "$DH_HOME" "$CACHE_DIR"

CONTROL_PLANES_FILE="$DH_HOME/control-planes.env"

usage() {
  cat <<EOF
Usage:
  dh update
  dh search [--service spark|airflow|starburst] [--apcode X] [--client X] [--envtype hprd|prod] [--env dev|int|qual|pprd|prod] [--namespace X] [--iks X]
  dh show <id>
  dh connect <id>
EOF
}

require_cmds() {
  for c in jq curl awk column; do
    command -v "$c" >/dev/null 2>&1 || {
      echo "Missing command: $c"
      exit 1
    }
  done
}

load_config() {
  if [[ ! -f "$CONTROL_PLANES_FILE" ]]; then
    cat > "$CONTROL_PLANES_FILE" <<'EOF'
# Control plane APIs
SPARK_CP_URL="https://spark-cp.example/api"
AIRFLOW_CP_URL="https://airflow-cp.example/api"
STARBURST_CP_URL="https://starburst-cp.example/api"

# Vault paths
SPARK_VAULT_PATH="secret/data/datahub/spark-cp"
AIRFLOW_VAULT_PATH="secret/data/datahub/airflow-cp"
STARBURST_VAULT_PATH="secret/data/datahub/starburst-cp"
EOF
    echo "Config template created: $CONTROL_PLANES_FILE"
    echo "Edit it before running dh update."
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$CONTROL_PLANES_FILE"
}

vault_get_credentials() {
  local vault_path="$1"

  # À adapter selon ton Vault CLI réel.
  # Format attendu en sortie :
  # client_id client_key
  local client_id client_key

  client_id="$(vault kv get -field=client_id "$vault_path")"
  client_key="$(vault kv get -field=client_key "$vault_path")"

  echo "$client_id $client_key"
}

get_token() {
  local base_url="$1"
  local vault_path="$2"

  read -r client_id client_key < <(vault_get_credentials "$vault_path")

  curl -sS -X POST "$base_url/auth" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg client_id "$client_id" \
      --arg client_key "$client_key" \
      '{client_id:$client_id, client_key:$client_key}')" \
  | jq -r '.token // .access_token'
}

fetch_cp() {
  local service="$1"
  local base_url="$2"
  local vault_path="$3"
  local out_json="$CACHE_DIR/${service}.json"

  echo "Fetching $service control plane..."

  local token
  token="$(get_token "$base_url" "$vault_path")"

  curl -sS "$base_url/instances" \
    -H "Authorization: Bearer $token" \
    -H "Accept: application/json" \
    > "$out_json"

  echo "$out_json"
}

normalize_spark() {
  local file="$1"

  jq -r '
    .instances[]? |
    [
      "spark",
      (.client // ""),
      (.apcode // .appCode // ""),
      (.envtype // .envType // ""),
      (.env // .environment // ""),
      (.namespace // ""),
      (.name // .instanceName // ""),
      (.version // ""),
      (.iks.version // .kubernetesVersion // ""),
      (.urls.sparkui // .urls.sparkUi // .sparkuiUrl // .url // ""),
      (.iks.name // .iksName // ""),
      (.ibm.account // .ibmAccount // ""),
      (.region // ""),
      "spark-cp"
    ] | @csv
  ' "$file"
}

normalize_airflow() {
  local file="$1"

  jq -r '
    .instances[]? |
    [
      "airflow",
      (.client // ""),
      (.apcode // .appCode // ""),
      (.envtype // .envType // ""),
      (.env // .environment // ""),
      (.namespace // ""),
      (.name // .instanceName // ""),
      (.version // .airflowVersion // ""),
      (.iks.version // .kubernetesVersion // ""),
      (.urls.webserver // .airflowUrl // .webUrl // .url // ""),
      (.iks.name // .iksName // ""),
      (.ibm.account // .ibmAccount // ""),
      (.region // ""),
      "airflow-cp"
    ] | @csv
  ' "$file"
}

normalize_starburst() {
  local file="$1"

  jq -r '
    .instances[]? |
    [
      "starburst",
      (.client // ""),
      (.apcode // .appCode // ""),
      (.envtype // .envType // ""),
      (.env // .environment // ""),
      (.namespace // ""),
      (.name // .instanceName // ""),
      (.version // .starburstVersion // ""),
      (.iks.version // .kubernetesVersion // ""),
      (.urls.portal // .coordinatorUrl // .webUrl // .url // ""),
      (.iks.name // .iksName // ""),
      (.ibm.account // .ibmAccount // ""),
      (.region // ""),
      "starburst-cp"
    ] | @csv
  ' "$file"
}

cmd_update() {
  require_cmds
  load_config

  local now
  now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local tmp
  tmp="$(mktemp)"

  echo 'id,service,client,apcode,envtype,env,namespace,instance_name,version,iks_version,url,iks_name,ibm_account,region,cp_source,updated_at' > "$tmp"

  spark_json="$(fetch_cp spark "$SPARK_CP_URL" "$SPARK_VAULT_PATH")"
  airflow_json="$(fetch_cp airflow "$AIRFLOW_CP_URL" "$AIRFLOW_VAULT_PATH")"
  starburst_json="$(fetch_cp starburst "$STARBURST_CP_URL" "$STARBURST_VAULT_PATH")"

  {
    normalize_spark "$spark_json"
    normalize_airflow "$airflow_json"
    normalize_starburst "$starburst_json"
  } | awk -v now="$now" '
    BEGIN { id=1 }
    {
      print id "," $0 ",\"" now "\""
      id++
    }
  ' >> "$tmp"

  mv "$tmp" "$MAPPING_FILE"

  echo "Mapping updated: $MAPPING_FILE"
}

cmd_search() {
  [[ -f "$MAPPING_FILE" ]] || {
    echo "Mapping not found. Run: dh update"
    exit 1
  }

  local service="" apcode="" client="" envtype="" env="" namespace="" iks=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --service) service="$2"; shift 2 ;;
      --apcode) apcode="$2"; shift 2 ;;
      --client) client="$2"; shift 2 ;;
      --envtype) envtype="$2"; shift 2 ;;
      --env) env="$2"; shift 2 ;;
      --namespace) namespace="$2"; shift 2 ;;
      --iks) iks="$2"; shift 2 ;;
      *) echo "Unknown option: $1"; exit 1 ;;
    esac
  done

  awk -F',' -v service="$service" \
            -v apcode="$apcode" \
            -v client="$client" \
            -v envtype="$envtype" \
            -v env="$env" \
            -v namespace="$namespace" \
            -v iks="$iks" '
    NR == 1 { next }

    function clean(x) {
      gsub(/^"|"$/, "", x)
      return x
    }

    {
      id=clean($1)
      svc=clean($2)
      cli=clean($3)
      app=clean($4)
      et=clean($5)
      e=clean($6)
      ns=clean($7)
      name=clean($8)
      iksv=clean($10)
      iksn=clean($12)
      acc=clean($13)

      if (service != "" && svc != service) next
      if (apcode != "" && app != apcode) next
      if (client != "" && cli !~ client) next
      if (envtype != "" && et != envtype) next
      if (env != "" && e != env) next
      if (namespace != "" && ns !~ namespace) next
      if (iks != "" && iksn !~ iks) next

      print id "|" svc "|" cli "|" app "|" et "/" e "|" ns "|" iksn "|" acc "|" iksv
    }
  ' "$MAPPING_FILE" | column -t -s '|'
}

get_line_by_id() {
  local id="$1"

  awk -F',' -v wanted="$id" '
    NR == 1 { next }
    $1 == wanted { print; found=1 }
    END { if (!found) exit 1 }
  ' "$MAPPING_FILE"
}

cmd_show() {
  local id="${1:-}"

  [[ -n "$id" ]] || {
    echo "Missing id"
    exit 1
  }

  [[ -f "$MAPPING_FILE" ]] || {
    echo "Mapping not found. Run: dh update"
    exit 1
  }

  local line
  line="$(get_line_by_id "$id")" || {
    echo "No instance found with id=$id"
    exit 1
  }

  echo "$line" | awk -F',' '
    function clean(x) {
      gsub(/^"|"$/, "", x)
      return x
    }

    {
      print "ID             : " clean($1)
      print "Service        : " clean($2)
      print "Client         : " clean($3)
      print "APCode         : " clean($4)
      print "EnvType/Env    : " clean($5) "/" clean($6)
      print "Namespace      : " clean($7)
      print "Instance       : " clean($8)
      print "Version        : " clean($9)
      print "IKS version    : " clean($10)
      print "URL            : " clean($11)
      print "IKS name       : " clean($12)
      print "IBM account    : " clean($13)
      print "Region         : " clean($14)
      print "Control plane  : " clean($15)
      print "Updated at     : " clean($16)
      print ""
      print "Connect command:"
      print "  iks " clean($12)
      print ""
      print "Namespace command:"
      print "  kubectl config set-context --current --namespace=" clean($7)
    }
  '
}

cmd_connect() {
  local id="${1:-}"

  [[ -n "$id" ]] || {
    echo "Missing id"
    exit 1
  }

  local iks_name
  iks_name="$(get_line_by_id "$id" | awk -F',' '{gsub(/^"|"$/, "", $12); print $12}')"

  echo "Executing: iks $iks_name"
  iks "$iks_name"
}

main() {
  local cmd="${1:-}"
  shift || true

  case "$cmd" in
    update) cmd_update "$@" ;;
    search) cmd_search "$@" ;;
    show) cmd_show "$@" ;;
    connect) cmd_connect "$@" ;;
    ""|-h|--help) usage ;;
    *) echo "Unknown command: $cmd"; usage; exit 1 ;;
  esac
}

main "$@"
```

---

## Exemple d’usage

```bash
dh update
```

Puis :

```bash
dh search --apcode A101737
dh search --service airflow --env prod
dh search --service spark --envtype hprd --client risk
```

Exemple de sortie :

```text
1  airflow   client-a  A101737  prod/prod   astronomer-a101737-prod-x1   iks-prod-fr-01   account-prod   1.29
2  spark     client-a  A101737  prod/prod   spark-a101737-prod-x1        iks-prod-fr-01   account-prod   1.29
```

Puis :

```bash
dh show 1
dh connect 1
```

---

## Point important

Le seul bloc à adapter à ton contexte réel est celui-ci :

```bash
vault kv get -field=client_id "$vault_path"
vault kv get -field=client_key "$vault_path"
```

Et les endpoints :

```bash
/auth
/instances
```

Si tes APIs renvoient des structures JSON différentes, il faut seulement ajuster les trois fonctions :

```bash
normalize_spark
normalize_airflow
normalize_starburst
```
