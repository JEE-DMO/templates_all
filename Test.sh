#!/usr/bin/env bash

set -euo pipefail

########################################
# Config
########################################
CSV_FILE="$(dirname "$0")/mapping.csv"

########################################
# Utils
########################################

error() {
    echo "❌ $1" >&2
    exit 1
}

usage() {
    cat <<EOF
Usage:
  $0 [-b BL] [-a APCD] [-e ENV] [-i IKS]

Filtres combinables:
  -b   BL
  -a   APCD
  -e   ENV
  -i   IKS (match partiel)

Exemples:
  $0 -b bcef
  $0 -a ap12279
  $0 -b bcef -e dev
  $0 -a ap12279 -e qual
EOF
    exit 0
}

########################################
# Vérifications
########################################

[ -f "$CSV_FILE" ] || error "CSV introuvable: $CSV_FILE"

########################################
# Auto détection séparateur CSV
########################################

detect_separator() {
    head -1 "$CSV_FILE" | grep -q ";" && echo ";" || echo ","
}

SEP=$(detect_separator)

########################################
# Lecture arguments
########################################

BL=""
APCD=""
ENV=""
IKS=""

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

########################################
# Filtrage CSV (mutualisé)
########################################

filter_csv() {
    awk -F"$SEP" \
        -v bl="$BL" \
        -v apcd="$APCD" \
        -v env="$ENV" \
        -v iks="$IKS" '
    BEGIN { IGNORECASE=1 }

    NR==1 {
        print
        next
    }

    {
        keep=1

        if (bl   != "" && $1 != bl)   keep=0
        if (apcd != "" && $2 != apcd) keep=0
        if (env  != "" && $3 != env)  keep=0
        if (iks  != "" && $7 !~ iks)  keep=0

        if (keep) print
    }' "$CSV_FILE"
}

########################################
# Affichage mutualisé
########################################

display() {
    RESULT=$(filter_csv)

    if [ "$(echo "$RESULT" | wc -l)" -le 1 ]; then
        echo "⚠️  Aucun résultat"
        exit 0
    fi

    echo "$RESULT" | column -t -s "$SEP"
}

########################################
# MAIN
########################################

display
