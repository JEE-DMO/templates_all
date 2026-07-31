Oui, l’hypothèse d’une **Variable Airflow contenant un JSON invalide** est très probable.

L’indice principal est que les 86 DAG échouent avec exactement la même erreur :

```text
JSONDecodeError: Expecting property name enclosed in double quotes
line 10 column 1 (char 431)
```

Cela indique généralement qu’un même JSON partagé est chargé pendant l’import de tous les DAG, par exemple avec :

```python
Variable.get("nom_variable", deserialize_json=True)
```

ou :

```python
json.loads(Variable.get("nom_variable"))
```

## Cause la plus probable

À la ligne 10, colonne 1, le parseur rencontre probablement une accolade `}` après une virgule finale :

```json
{
  "host": "server",
  "port": 443,
}
```

La virgule après `443` est interdite en JSON. La version correcte est :

```json
{
  "host": "server",
  "port": 443
}
```

L’erreur peut aussi venir de clés avec des apostrophes ou sans guillemets :

```text
{
  'host': 'server'
}
```

ou :

```text
{
  host: "server"
}
```

En JSON strict, il faut obligatoirement :

```json
{
  "host": "server"
}
```

## Recherche Notepad++ pour les virgules finales

Dans **Rechercher → Rechercher**, sélectionnez **Expression régulière**, puis utilisez :

```regex
,\h*\R\h*[}\]]
```

Cela repère notamment :

```json
"value": "test",
}
```

et :

```json
"item",
]
```

Pour rechercher aussi lorsque l’accolade est sur la même ligne :

```regex
,\s*[}\]]
```

Vérifiez que l’option **« . correspond à nouvelle ligne »** n’est pas nécessairement cochée.

## Recherche des clés non entourées de guillemets

```regex
^\h*[A-Za-z_][A-Za-z0-9_.-]*\h*:
```

Cela détectera par exemple :

```text
host: "server"
```

## Recherche des apostrophes utilisées comme du JSON

```regex
'[^'\r\n]*'\h*:
```

ou plus simplement :

```regex
'
```

Attention : une apostrophe peut être légitime dans une valeur textuelle. Il faut vérifier le contexte.

## Point important sur l’export Airflow

L’export complet des variables Airflow peut être lui-même un JSON valide, alors qu’une valeur interne est invalide.

Exemple :

```json
{
  "my_variable": "{\"host\": \"server\",}"
}
```

Le fichier d’export extérieur peut être valide, car la valeur est une chaîne de caractères. Mais lorsque le DAG fait :

```python
Variable.get("my_variable", deserialize_json=True)
```

la chaîne interne échoue à cause de la virgule finale.

Il faut donc valider **chaque valeur de variable**, et pas seulement le fichier d’export global.

## Validation automatique de toutes les variables exportées

Avec un script Python :

```python
import json
from pathlib import Path

export_file = Path("variables.json")

with export_file.open(encoding="utf-8") as file:
    variables = json.load(file)

for variable_name, value in variables.items():
    if not isinstance(value, str):
        continue

    stripped_value = value.strip()

    if not stripped_value.startswith(("{", "[")):
        continue

    try:
        json.loads(stripped_value)
    except json.JSONDecodeError as error:
        print(f"\nVariable invalide : {variable_name}")
        print(f"Ligne : {error.lineno}")
        print(f"Colonne : {error.colno}")
        print(f"Position : {error.pos}")
        print(f"Erreur : {error.msg}")
```

Il affichera directement les variables dont la valeur ressemble à du JSON mais n’est pas valide.

## Diagnostic le plus efficace côté code

Recherchez dans le dépôt :

```text
deserialize_json=True
```

puis :

```text
json.loads(
```

Les 86 DAG utilisent probablement :

* une même Variable Airflow ;
* une fonction utilitaire commune ;
* un fichier de configuration commun importé au chargement des DAG.

Comme l’erreur est toujours à **`line 10 column 1 char 431`**, il s’agit presque certainement du **même contenu JSON partagé**, et non de 86 erreurs différentes. Commencez par regarder le caractère au début de la ligne 10 : s’il s’agit de `}`, la virgule finale à la ligne précédente est la cause la plus probable.
