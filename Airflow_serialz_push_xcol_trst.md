```python
from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime, date
from typing import Optional, List
import json


@dataclass
class SchemaHealth:
    catalog: str
    schema: str
    is_healthy: bool
    error: Optional[str] = None


@dataclass
class CatalogHealth:
    catalog: str
    is_healthy: bool
    schemas: List[SchemaHealth] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class InstanceHealthReport:
    instance_name: str
    env: str
    url: str
    status: str
    is_query_working: bool = False
    active_workers: int = None
    total_workers: int = None
    version: str = "unknown"
    uptime: str = "unknown"
    is_coordinator_healthy: bool = False
    error_message: Optional[str] = None
    checked_at: datetime = None
    catalogs: List[CatalogHealth] = field(default_factory=list)
    ibm_account: str = "TBD"
    cluster_name: str = "TBD"

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()


def to_xcom_safe(obj):
    if is_dataclass(obj):
        return to_xcom_safe(asdict(obj))

    if isinstance(obj, list):
        return [to_xcom_safe(item) for item in obj]

    if isinstance(obj, dict):
        return {key: to_xcom_safe(value) for key, value in obj.items()}

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    return obj


def main():
    report = InstanceHealthReport(
        instance_name="starburst-dev-001",
        env="DEV",
        url="starburst-dev.example.net",
        status="HEALTHY",
        is_query_working=True,
        active_workers=4,
        total_workers=4,
        version="435-e",
        uptime="2d 4h",
        is_coordinator_healthy=True,
        catalogs=[
            CatalogHealth(
                catalog="iceberg",
                is_healthy=True,
                schemas=[
                    SchemaHealth(
                        catalog="iceberg",
                        schema="default",
                        is_healthy=True
                    ),
                    SchemaHealth(
                        catalog="iceberg",
                        schema="finance",
                        is_healthy=False,
                        error="Access denied"
                    )
                ]
            )
        ],
        ibm_account="account-dev",
        cluster_name="iks-dev-01"
    )

    reports = [to_xcom_safe(report)]

    print("=== XCOM SAFE OBJECT ===")
    print(json.dumps(reports, indent=2, ensure_ascii=False))

    print("\n=== JSON SERIALIZATION TEST ===")
    json.dumps(reports)
    print("OK - compatible XCom JSON")


if __name__ == "__main__":
    main()
```

Exécution :

```bash
python test_xcom_safe.py
```

