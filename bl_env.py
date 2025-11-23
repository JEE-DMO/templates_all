from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime

def aggregate_health_summary(health_statuses: List[HealthStatus]) -> Dict[str, Any]:
    total = len(health_statuses)
    healthy = sum(s.is_healthy for s in health_statuses)

    env_stats = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})
    bl_stats = defaultdict(lambda: {'total': 0, 'healthy': 0, 'unhealthy': 0})

    for s in health_statuses:
        env, bl = s.instance.environment, s.instance.business_line
        for stats in (env_stats[env], bl_stats[bl]):
            stats['total'] += 1
            stats['healthy'] += s.is_healthy
            stats['unhealthy'] += not s.is_healthy

    return {
        'total_instances': total,
        'healthy_instances': healthy,
        'unhealthy_instances': total - healthy,
        'health_percentage': round((healthy / total * 100), 2) if total else 0,
        'by_environment': dict(env_stats),
        'by_business_line': dict(bl_stats),
        'checked_at': datetime.now().isoformat()
    }
