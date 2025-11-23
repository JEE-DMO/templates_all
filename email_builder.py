from typing import List, Dict, Any
from datetime import datetime
from airflow_health.models import AirflowInstance, HealthStatus

def build_environment_details_html(summary: Dict[str, Any], by_key: str) -> str:
    html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:20px;">'
    
    for key, stats in summary[by_key].items():
        pct = round((stats['healthy']/stats['total']*100) if stats['total'] else 0, 2)
        style = "background-color:#d6f3e4;border-left:4px solid #0f8b4b;" if pct > 80 else "background-color:#f8d7da;border-left:4px solid #d43f3a;"

        html += f'''
        <div style="padding:15px;border-radius:5px;text-align:center;{style}">
            <h3 style="margin:0 0 10px 0;color:#666;font-size:14px;">{key}</h3>
            <div style="font-size:32px;font-weight:bold;color:#003366;">{stats['healthy']}/{stats['total']}</div>
        </div>
        '''

    html += '</div>'
    return html


def build_instance_row_html(status: HealthStatus) -> str:
    instance = status.instance

    if status.is_healthy:
        status_badge = f'<span style="padding:2px 4px;border-radius:3px;font-size:12px;font-weight:600;background-color:#0f8b4b;color:white;">✅</span>'
    else:
        status_badge = f'<span style="padding:2px 4px;border-radius:3px;font-size:12px;font-weight:600;background-color:#d43f3a;color:white;">❌</span>'

    def comp_badge(text):
        if text == "healthy":
            return '<span style="display:inline-block;padding:2px 6px;border-radius:2px;font-size:11px;margin:2px;background-color:#d6f3e4;color:#0f8b4b;">✅</span>'
        if text == "N/A":
            return '<span style="display:inline-block;padding:2px 6px;border-radius:2px;font-size:11px;margin:2px;">⚠️</span>'
        return f'<span style="display:inline-block;padding:2px 6px;border-radius:2px;font-size:11px;margin:2px;background-color:#f8d7da;color:#721c24;">❌</span>'

    error_cell = f'<span style="color:#d43f3a;font-size:12px;font-style:italic;">{status.error_message}</span>' if status.error_message else '-'

    return f'''
    <tr style="border-bottom:1px solid #ddd;">
        <td><strong>{instance.business_line}</strong></td>
        <td><strong>{instance.environment}</strong></td>
        <td><a href="{instance.url}">{instance.url}</a></td>
        <td>{instance.version}</td>
        <td>{status_badge}</td>
        <td>{comp_badge(status.dag_processor_status)}</td>
        <td>{comp_badge(status.scheduler_status)}</td>
        <td>{comp_badge(status.triggerer_status)}</td>
        <td>{comp_badge(status.metadatabase_status)}</td>
        <td>{error_cell}</td>
    </tr>
    '''


def build_html_report(health_statuses: List[HealthStatus], summary: Dict[str, Any], environment_label: str) -> str:

    instances_rows = '\n'.join([build_instance_row_html(status) for status in sorted(health_statuses, key=lambda s: s.instance.business_line)])
    environment_details = build_environment_details_html(summary, "by_environment")
    business_line_details = build_environment_details_html(summary, "by_business_line")
    
    html = HTML_TEMPLATE.format(
        environment_label=environment_label,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_instances=summary['total_instances'],
        healthy_instances=summary['healthy_instances'],
        unhealthy_instances=summary['unhealthy_instances'],
        health_percentage=summary['health_percentage'],
        environment_details=environment_details,
        business_line_details=business_line_details,
        instances_rows=instances_rows
    )
    
    return html


def get_email_subject(summary: Dict[str, Any], environment_label: str) -> str:

    status_emoji = "✅" if summary['unhealthy_instances'] == 0 else "⚠️"
    return (f"{status_emoji} Airflow Health Report [{environment_label}] - "
            f"{summary['healthy_instances']}/{summary['total_instances']} OK "

            f"({summary['health_percentage']}%)")

