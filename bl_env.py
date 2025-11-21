from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime

def aggregate_health_summary(health_statuses: List[HealthStatus]) -> Dict[str, Any]:
    total_instances = len(health_statuses)
    healthy_instances = sum(status.is_healthy for status in health_statuses)

    by_environment = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})
    by_business_line = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})

    for status in health_statuses:
        env = status.instance.environment
        bl = status.instance.business_line
        is_healthy = bool(status.is_healthy)

        # Environment aggregation
        by_environment[env]['total'] += 1
        by_environment[env]['healthy'] += int(is_healthy)
        by_environment[env]['unhealthy'] += int(not is_healthy)

        # Business line aggregation
        by_business_line[bl]['total'] += 1
        by_business_line[bl]['healthy'] += int(is_healthy)
        by_business_line[bl]['unhealthy'] += int(not is_healthy)

    return {
        'total_instances': total_instances,
        'healthy_instances': healthy_instances,
        'unhealthy_instances': total_instances - healthy_instances,
        'by_environment': dict(by_environment),
        'by_business_line': dict(by_business_line),
        'checked_at': datetime.now().isoformat()
    }
