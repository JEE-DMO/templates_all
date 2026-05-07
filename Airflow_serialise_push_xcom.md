```python
from dataclasses import asdict, is_dataclass
from datetime import datetime, date


def to_xcom_safe(obj):
    """
    Convert recursively every dataclass/object into JSON-safe structure
    for Airflow XCom.
    """

    if is_dataclass(obj):
        return to_xcom_safe(asdict(obj))

    if isinstance(obj, list):
        return [to_xcom_safe(item) for item in obj]

    if isinstance(obj, dict):
        return {
            key: to_xcom_safe(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    return obj
```

Puis remplacer :

```python
reports.append(asdict(report))
```

par :

```python
reports.append(to_xcom_safe(report))
```

Et garder :

```python
context["ti"].xcom_push(
    key="starburst_reports",
    value=reports
)
```

Optionnel mais fortement recommandé avant le push pour vérifier immédiatement :

```python
import json

json.dumps(reports)
```

Si ça passe, ton XCom est propre.
