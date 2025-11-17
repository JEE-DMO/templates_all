import requests
from typing import List, Dict, Any
from datetime import datetime
import logging
from collections import defaultdict

from airflow_health.models import AirflowInstance, HealthStatus


logger = logging.getLogger(__name__)

def check_all_instances(instances: List[AirflowInstance]) -> List[HealthStatus]:
    return list(check_instance_health(inst) for inst in instances)


def check_instance_health(instance: AirflowInstance, timeout: int = 10) -> HealthStatus:
    h = HealthStatus(instance=instance, status_code=None)

    try:
        r = requests.get(instance.health_url, timeout=timeout)
        h.status_code = r.status_code

        if r.ok:
            d = r.json()
            h.scheduler_status     = d.get("scheduler", {}).get("status", "N/A")
            h.dag_processor_status = d.get("dag_processor", {}).get("status", "N/A")
            h.triggerer_status     = d.get("triggerer", {}).get("status", "N/A")
            h.metadatabase_status  = d.get("metadatabase", {}).get("status", "N/A")
        else:
            h.error_message = (r.text or "")[:200]

    except requests.exceptions.Timeout:
        h.status_code = 408
        h.error_message = "Timeout"

    except Exception as e:
        h.status_code = 500
        h.error_message = str(e)

    return h



def aggregate_health_summary(health_statuses: List[HealthStatus]) -> Dict[str, Any]:
    total = len(health_statuses)
    healthy = sum(s.is_healthy for s in health_statuses)
    by_env = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})
    
    [by_env[s.instance.environment].update({
        'total': by_env[s.instance.environment]['total'] + 1,
        'healthy': by_env[s.instance.environment]['healthy'] + int(s.is_healthy),
        'unhealthy': by_env[s.instance.environment]['unhealthy'] + int(not s.is_healthy)
    }) for s in health_statuses]

 
    return {
        'total_instances': total,
        'healthy_instances': healthy,
        'unhealthy_instances': total - healthy,
        'health_percentage': round((healthy / total * 100), 2) if total else 0,
        'by_environment': dict(by_env),
        'checked_at': datetime.now().isoformat()
    }
    
    
def get_instances_from_airflowClient(airflowClient_command: str, environments: List[str]) -> List[AirflowInstance]:
    
    logger.info(f"Récupération des instances pour les environnements: {environments}")
    instances_data = get_running_instances(environments)
    
    instances = [
        AirflowInstance(
            app_code=data['app_code'],
            release=data['release'],
            version=data['version'],
            uid=data['uid'],
            environment=data['environment']
        )
        for data in instances_data
    ]
    
    logger.info(f"{len(instances)} instances récupérées")
    return instances


