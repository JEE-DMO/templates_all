# Question Custom CodinGame — Pipeline de Validation de Données

**Niveau :** Expert · Python uniquement  
**Durée suggérée :** 15 minutes  
**Total :** 600 pts

---

## Contexte

Vous travaillez sur un **pipeline de validation de données** en mémoire. Des enregistrements bruts arrivent sous forme de dictionnaires et doivent passer par une série de transformations et de contrôles avant d'être acceptés ou rejetés.

Le pipeline est défini par trois composants :

**1. Un schéma de validation** — chaque champ a un type attendu et une règle optionnelle.  
**2. Un générateur de records** — les enregistrements arrivent en flux, un par un.  
**3. Un contexte d'exécution** — le pipeline s'exécute dans un bloc `with` qui mesure le nombre de records traités et intercepte les erreurs sans interrompre le flux.

### Règles métier

Un record est un dictionnaire avec les clés : `id` (int), `value` (float), `label` (str).

Un record est **valide** si :
- tous les types correspondent au schéma,
- `value` est dans l'intervalle `[0.0, 1000.0]`,
- `label` est une chaîne non vide,
- `id` est strictement positif.

Un record **invalide** est compté mais non retourné.

### Exemple

```
Entrée (3 records) :
{"id": 1, "value": 42.5, "label": "alpha"}   → valide
{"id": -1, "value": 42.5, "label": "beta"}   → invalide (id <= 0)
{"id": 2, "value": 1500.0, "label": "gamma"} → invalide (value hors intervalle)

Sortie :
valid=1 invalid=2
```

---

## Objectif

Complétez les parties manquantes du code de départ pour que `process_pipeline(raw_records)` retourne un tuple `(valid_count, invalid_count)`.

### Contraintes

- `0 < nombre de records < 100 000`
- Les records invalides ne lèvent pas d'exception : ils sont silencieusement comptés
- La fonction `process_pipeline` doit utiliser **tous** les composants fournis
- Ne pas modifier les signatures ni la structure du `main()`

---

## Code de départ

```python
import sys
import time
from contextlib import contextmanager
from typing import Iterator, Any, Generator
from collections.abc import Callable


# ── 1. DESCRIPTOR ─────────────────────────────────────────────────────────────
# Valide le type d'un attribut à l'affectation.
class TypedField:
    def __init__(self, expected_type: type) -> None:
        self.expected_type = expected_type
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, objtype: type = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(self.name)

    def __set__(self, obj: Any, value: Any) -> None:
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} attend {self.expected_type.__name__}, "
                f"reçu {type(value).__name__}"
            )
        obj.__dict__[self.name] = value


# ── 2. METACLASS ──────────────────────────────────────────────────────────────
# Collecte automatiquement tous les TypedField déclarés dans la classe.
class SchemaMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> "SchemaMeta":
        fields = {
            k: v
            for k, v in namespace.items()
            if isinstance(v, TypedField)
        }
        namespace["_fields"] = fields
        return super().__new__(mcs, name, bases, namespace)


# ── 3. SCHEMA (metaclass + descriptors) ───────────────────────────────────────
class RecordSchema(metaclass=SchemaMeta):
    id    = TypedField(int)
    value = TypedField(float)
    label = TypedField(str)


# ── 4. DECORATOR ──────────────────────────────────────────────────────────────
# Applique les règles métier après la validation de type.
def business_rules(func: Callable) -> Callable:
    def wrapper(record: dict) -> bool:
        if not func(record):
            return False
        # Règles métier à vérifier ici :
        # • id > 0
        # • 0.0 <= value <= 1000.0
        # • label non vide
        # TODO : compléter
        return True
    return wrapper


# ── 5. GENERATOR ──────────────────────────────────────────────────────────────
# Produit les records un par un depuis une liste brute.
def record_stream(raw: list[dict]) -> Generator[dict, None, None]:
    # TODO : compléter (yield chaque élément de raw)
    pass


# ── 6. CONTEXT MANAGER ────────────────────────────────────────────────────────
# Mesure le nombre total de records traités et intercepte les erreurs.
@contextmanager
def pipeline_context(label: str) -> Iterator[dict]:
    state = {"processed": 0, "errors": 0}
    try:
        # TODO : yield state pour que le bloc with puisse l'incrémenter
        pass
    except Exception as e:
        print(f"[{label}] Erreur pipeline : {e}", file=sys.stderr)
    finally:
        print(
            f"[{label}] processed={state['processed']} errors={state['errors']}",
            file=sys.stderr,
        )


# ── 7. VALIDATION (type-check via schema) ─────────────────────────────────────
def type_check(record: dict) -> bool:
    schema = RecordSchema()
    try:
        for field_name, descriptor in RecordSchema._fields.items():
            descriptor.__set__(schema, record.get(field_name))
        return True
    except TypeError:
        return False


# ── 8. FONCTION PRINCIPALE ────────────────────────────────────────────────────
@business_rules
def validate(record: dict) -> bool:
    return type_check(record)


def process_pipeline(raw_records: list[dict]) -> tuple[int, int]:
    valid, invalid = 0, 0

    with pipeline_context("DataPipeline") as state:
        for record in record_stream(raw_records):
            # TODO : incrémenter state["processed"]
            #        appeler validate(record)
            #        incrémenter valid ou invalid selon le résultat
            pass

    return valid, invalid


# ── NE PAS MODIFIER ───────────────────────────────────────────────────────────
def main() -> None:
    n = int(input())
    raw: list[dict] = []
    for _ in range(n):
        line = input().split(",")
        raw.append({
            "id":    int(line[0]),
            "value": float(line[1]),
            "label": line[2].strip(),
        })
    with pipeline_context.__wrapped__ if hasattr(pipeline_context, "__wrapped__") \
         else __import__("contextlib").nullcontext():
        pass
    valid, invalid = process_pipeline(raw)
    print(f"valid={valid} invalid={invalid}")


if __name__ == "__main__":
    main()
```

---

## Ce que le candidat doit compléter

| Zone | Fonctionnalité | Description |
|------|---------------|-------------|
| `business_rules` → `wrapper` | **Decorator** | Ajouter les 3 contrôles métier (`id > 0`, `value` dans `[0, 1000]`, `label` non vide) |
| `record_stream` | **Generator** | `yield` chaque élément de `raw` |
| `pipeline_context` | **Context manager** | `yield state`, gérer `try/finally` |
| `process_pipeline` | **`with` + tout** | Incrémenter `state["processed"]`, appeler `validate`, compter `valid`/`invalid` |

Les composants `TypedField` (descriptor), `SchemaMeta` (metaclass), `RecordSchema`, `type_check` et `typing` sont fournis et **ne doivent pas être modifiés**.

---

## Critères d'évaluation

| Critère | Description | Points |
|---------|-------------|--------|
| Cas de base valide | Tous les records sont valides | +60 pts |
| Cas de base invalide | Tous les records sont invalides | +60 pts |
| Règle `id <= 0` | Détection correcte des ids non positifs | +65 pts |
| Règle `value` hors intervalle | Valeurs < 0.0 ou > 1000.0 rejetées | +65 pts |
| Règle `label` vide | Chaîne vide ou espaces seuls rejetés | +65 pts |
| Type mismatch | Mauvais type sur `id`, `value` ou `label` | +65 pts |
| Mix valide / invalide | Comptage exact sur flux hétérogène | +70 pts |
| Grand volume (10⁵ records) | Pas de chargement complet en mémoire | +70 pts |
| **Total** | | **580 pts** |

---

## Notes pour l'évaluateur

### Solution de référence

```python
# business_rules → wrapper
def wrapper(record: dict) -> bool:
    if not func(record):
        return False
    if record.get("id", 0) <= 0:
        return False
    if not (0.0 <= record.get("value", -1) <= 1000.0):
        return False
    if not str(record.get("label", "")).strip():
        return False
    return True

# record_stream
def record_stream(raw):
    for item in raw:
        yield item

# pipeline_context
@contextmanager
def pipeline_context(label):
    state = {"processed": 0, "errors": 0}
    try:
        yield state
    except Exception as e:
        state["errors"] += 1
        print(f"[{label}] Erreur pipeline : {e}", file=sys.stderr)
    finally:
        print(
            f"[{label}] processed={state['processed']} errors={state['errors']}",
            file=sys.stderr,
        )

# process_pipeline
def process_pipeline(raw_records):
    valid, invalid = 0, 0
    with pipeline_context("DataPipeline") as state:
        for record in record_stream(raw_records):
            state["processed"] += 1
            if validate(record):
                valid += 1
            else:
                invalid += 1
    return valid, invalid
```

### Ce que chaque zone révèle

- **Decorator** (`business_rules`) : maîtrise du pattern wrapper, compréhension de la chaîne de validation, soin sur les cas limites (valeur manquante, `None`).
- **Generator** (`record_stream`) : compréhension de `yield` vs `return`, conscience de la consommation mémoire sur grand volume.
- **Context manager** (`pipeline_context`) : usage de `@contextmanager`, gestion `try/except/finally`, état mutable partagé via `yield`.
- **`with` + assembly** (`process_pipeline`) : capacité à assembler tous les composants sans en briser un seul, lecture du flux sans accumuler.
- **Descriptor + Metaclass** (fournis, mais à lire) : le candidat doit comprendre `RecordSchema._fields` pour ne pas casser `type_check` — révèle sa capacité à lire du code avancé qu'il n'a pas écrit.
- **Typing** (présent dans les signatures) : un candidat expert enrichira spontanément ses ajouts avec des annotations cohérentes.

### Signaux d'un candidat expert

- Utilise `record.get(key, default)` plutôt que `record[key]` dans le decorator (robustesse).
- Ne stocke pas tous les records en mémoire dans `record_stream` (inutile puisque `raw` est déjà en mémoire, mais le réflexe de `yield` plutôt que `return list(...)` est révélateur).
- Incrémente `state["errors"]` dans le `except` du context manager sans qu'on le lui demande explicitement.
- Ajoute ses propres annotations de type sur les fonctions complétées.
