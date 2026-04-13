Voici les deux approches avec leurs diagrammes et le code complet.

---

## Solution 1 — `skip_holidays` task en tête de DAG

Le principe : une `ShortCircuitOperator` évalue si le `logical_date` est un jour férié. Si oui, elle renvoie `False` et toutes les tâches en aval sont skippées. Sinon elle laisse passer le flux normalement.```python
from airflow import DAG
from airflow.operators.python import ShortCircuitOperator, PythonOperator
from datetime import datetime
import holidays

def _is_working_day(**context) -> bool:
    """Retourne False si jour férié → short-circuit (skip aval)."""
    execution_date = context["logical_date"].date()
    fr_holidays = holidays.France(years=execution_date.year)
    if execution_date in fr_holidays:
        holiday_name = fr_holidays.get(execution_date)
        print(f"Jour férié détecté : {holiday_name} — DAG skippé.")
        return False
    return True

with DAG(
    dag_id="my_dag_with_holiday_skip",
    schedule="0 8 * * 1-5",   # lundi–vendredi, 08h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    skip_holidays = ShortCircuitOperator(
        task_id="skip_holidays",
        python_callable=_is_working_day,
        ignore_downstream_trigger_rules=True,  # force le skip sur tout l'aval
    )

    t1 = PythonOperator(task_id="T1", python_callable=lambda: print("T1"))
    t2 = PythonOperator(task_id="T2", python_callable=lambda: print("T2"))
    t3 = PythonOperator(task_id="T3", python_callable=lambda: print("T3"))
    t4 = PythonOperator(task_id="T4", python_callable=lambda: print("T4"))
    t5 = PythonOperator(task_id="T5", python_callable=lambda: print("T5"))

    skip_holidays >> t1 >> [t2, t3] >> [t4, t5]
```

Le paramètre `ignore_downstream_trigger_rules=True` est essentiel : sans lui, les tâches avec `trigger_rule` non-default (ex. `all_done`) pourraient quand même s'exécuter malgré le skip.

---

## Solution 2 — Custom `Timetable`

Ici la logique jour férié est portée par le scheduler lui-même : Airflow ne crée même pas de `DagRun` les jours fériés. Le DAG reste inchangé (`T1 >> [T2,T3] >> [T4,T5]`).```python
# plugins/workday_timetable.py
from airflow.plugins_manager import AirflowPlugin
from airflow.timetables.base import DagRunInfo, DataInterval, TimeRestriction, Timetable
from pendulum import DateTime, instance, timezone
import holidays

PARIS_TZ = timezone("Europe/Paris")

class WorkdayTimetable(Timetable):
    """Timetable quotidienne excluant week-ends et jours fériés français."""

    description = "Tous les jours ouvrés (hors fériés FR)"

    def __init__(self, hour: int = 8, minute: int = 0):
        self._hour = hour
        self._minute = minute

    def _next_workday(self, from_dt: DateTime) -> DateTime:
        """Avance jusqu'au prochain jour ouvré."""
        candidate = from_dt.add(days=1).set(
            hour=self._hour, minute=self._minute, second=0, microsecond=0
        )
        fr_holidays = holidays.France(years=candidate.year)
        while candidate.day_of_week >= 5 or candidate.date() in fr_holidays:
            candidate = candidate.add(days=1).set(
                hour=self._hour, minute=self._minute, second=0, microsecond=0
            )
            fr_holidays = holidays.France(years=candidate.year)
        return candidate

    def next_dagrun_info(
        self,
        *,
        last_automated_data_interval: DataInterval | None,
        restriction: TimeRestriction,
    ) -> DagRunInfo | None:
        if last_automated_data_interval is None:
            # Premier run : on part de start_date
            start = restriction.earliest
            if start is None:
                return None
            next_run = start.in_timezone(PARIS_TZ).set(
                hour=self._hour, minute=self._minute, second=0, microsecond=0
            )
        else:
            next_run = self._next_workday(
                last_automated_data_interval.end.in_timezone(PARIS_TZ)
            )

        if restriction.latest is not None and next_run > restriction.latest:
            return None

        return DagRunInfo.interval(
            start=next_run,
            end=next_run,
        )

    def serialize(self):
        return {"hour": self._hour, "minute": self._minute}

    @classmethod
    def deserialize(cls, data):
        return cls(hour=data["hour"], minute=data["minute"])


class WorkdayTimetablePlugin(AirflowPlugin):
    name = "workday_timetable_plugin"
    timetables = [WorkdayTimetable]
```

```python
# dags/my_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from plugins.workday_timetable import WorkdayTimetable

with DAG(
    dag_id="my_dag_timetable",
    timetable=WorkdayTimetable(hour=8, minute=0),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    t1 = PythonOperator(task_id="T1", python_callable=lambda: print("T1"))
    t2 = PythonOperator(task_id="T2", python_callable=lambda: print("T2"))
    t3 = PythonOperator(task_id="T3", python_callable=lambda: print("T3"))
    t4 = PythonOperator(task_id="T4", python_callable=lambda: print("T4"))
    t5 = PythonOperator(task_id="T5", python_callable=lambda: print("T5"))

    t1 >> [t2, t3] >> [t4, t5]
```

---

## Comparatif des deux approches

| Critère | Solution 1 — `skip_holidays` | Solution 2 — `Timetable` |
|---|---|---|
| DagRun créé ? | Oui (avec tasks skippées) | Non — aucune trace |
| Historique Airflow UI | Visible, état "skipped" | Run absent |
| Complexité implem. | Faible | Moyenne (plugin) |
| Logique centralisée | Dans le DAG | Dans le plugin (réutilisable) |
| Nb de DAGs concernés | 1 par ajout de task | Tous les DAGs utilisant la timetable |
| `catchup` / backfill | Fonctionne normalement | Respecte aussi le calendrier |

Pour une plateforme OAAS partagée avec plusieurs clients et plusieurs DAGs, la `Timetable` est la solution la plus propre : la logique est définie une seule fois dans un plugin, et n'importe quel DAG client peut y souscrire avec `timetable=WorkdayTimetable()`. La solution `skip_holidays` est préférable si vous voulez garder la trace des exécutions dans l'UI même les jours fériés.
