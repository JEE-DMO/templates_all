from typing import List, Dict, Any
from datetime import datetime
from airflow_health.models import AirflowInstance, HealthStatus


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f2f5; /* gris BNP */
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #003366; /* bleu BNP */
            border-bottom: 3px solid #0f8b4b; /* vert BNP */
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .summary-card.healthy {{
            background-color: #d6f3e4; /* vert clair BNP */
            border-left: 4px solid #0f8b4b; /* vert BNP */
        }}
        .summary-card.unhealthy {{
            background-color: #f8d7da; /* rouge clair */
            border-left: 4px solid #d43f3a; /* rouge BNP */
        }}
        .summary-card.total {{
            background-color: #e0edf7; /* bleu clair BNP */
            border-left: 4px solid #003366; /* bleu BNP */
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #003366;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #003366; /* bleu BNP */
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f2f6fa; /* survol bleu très clair */
        }}
        .status-badge {{
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-healthy {{
            background-color: #0f8b4b; /* vert BNP */
            color: white;
        }}
        .status-unhealthy {{
            background-color: #d43f3a; /* rouge BNP */
            color: white;
        }}
        .status-warning {{
            background-color: #ffdd57; /* jaune BNP */
            color: #333;
        }}
        .component-status {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 2px;
            font-size: 11px;
            margin: 2px;
        }}
        .component-healthy {{
            background-color: #d6f3e4; /* vert clair */
            color: #0f8b4b;         /* vert BNP */
        }}
        .component-unhealthy {{
            background-color: #f8d7da; /* rouge clair */
            color: #721c24;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
        .error-message {{
            color: #d43f3a; /* rouge BNP */
            font-size: 12px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Rapport de Santé Airflow - {environment_label}</h1>
        <p><strong>Généré le:</strong> {timestamp}</p>
        <div class="summary">
            <div class="summary-card total">
                <h3>Total Instances</h3>
                <div class="value">{total_instances}</div>
            </div>
            <div class="summary-card healthy">
                <h3>Instances OK</h3>
                <div class="value">{healthy_instances}</div>
            </div>
            <div class="summary-card unhealthy">
                <h3>Instances KO</h3>
                <div class="value">{unhealthy_instances}</div>
            </div>
            <div class="summary-card total">
                <h3>Taux de Santé</h3>
                <div class="value">{health_percentage}%</div>
            </div>
        </div>

        <h2>📊 Détail par Environnement</h2>
        {environment_details}

        <h2>📋 Détail des Instances</h2>
        <table>
            <thead>
                <tr>
                    <th>EQUIPE</th>
                    <th>ENV</th>
                    <th>URL</th>
                    <th>VERSION</th>
                    <th>HTTP</th>
                    <th>DAG_PROCESSOR</th>
                    <th>SCHEDULER</th>
                    <th>TRIGGER</th>
                    <th>META_DB</th>
                    <th>ERROR</th>
                </tr>
            </thead>
            <tbody>
                {instances_rows}
            </tbody>
        </table>

        <div class="footer">
            <p>Ce rapport a été généré automatiquement par le DAG Airflow Health Monitor.</p>
            <p>Pour plus d'informations, consultez la documentation interne.</p>
        </div>
    </div>
</body>
</html>
"""


def build_environment_details_html(summary: Dict[str, Any]) -> str:
    html = '<div class="summary">'
    
    for env, stats in summary['by_environment'].items():
        health_pct = round((stats['healthy'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2)
        card_class = 'healthy' if health_pct > 80 else 'unhealthy'
        
        html += f'''
        <div class="summary-card {card_class}">
            <h3>{env}</h3>
            <div class="value">{stats['healthy']}/{stats['total']}</div>
            <div>{health_pct}%</div>
        </div>
        '''
    
    html += '</div>'
    return html


def build_instance_row_html(status: HealthStatus) -> str:

    instance = status.instance

    if status.is_healthy:
        status_badge = f'<span class="status-badge status-healthy">✓ {status.status_code}</span>'
    else:
        status_badge = f'<span class="status-badge status-unhealthy">✗ {status.status_code}</span>'

    def component_badge(status_text):
        if status_text == "healthy":
            return f'<span class="component-status component-healthy">✓ OK</span>'
        elif status_text == "N/A":
            return f'<span class="component-status">N/A</span>'
        else:
            return f'<span class="component-status component-unhealthy">✗ {status_text}</span>'
    
    error_cell = f'<span class="error-message">{status.error_message}</span>' if status.error_message else '-'
    
    return f'''
    <tr>
        <td><strong>{instance.team}</strong></td>
        <td><strong>{instance.environment}</strong></td>
        <td><a href="{instance.url}">{instance.url}</a></td>
        <td>{instance.version}</td>
        <td>{status_badge}</td>
        <td>{component_badge(status.dag_processor_status)}</td>
        <td>{component_badge(status.scheduler_status)}</td>
        <td>{component_badge(status.triggerer_status)}</td>
        <td>{component_badge(status.metadatabase_status)}</td>
        <td>{error_cell}</td>
    </tr>
    '''


def build_html_report(health_statuses: List[HealthStatus], summary: Dict[str, Any], environment_label: str) -> str:

    instances_rows = '\n'.join([build_instance_row_html(status) for status in health_statuses])
    environment_details = build_environment_details_html(summary)
    
    html = HTML_TEMPLATE.format(
        environment_label=environment_label,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_instances=summary['total_instances'],
        healthy_instances=summary['healthy_instances'],
        unhealthy_instances=summary['unhealthy_instances'],
        health_percentage=summary['health_percentage'],
        environment_details=environment_details,
        instances_rows=instances_rows
    )
    
    return html


def get_email_subject(summary: Dict[str, Any], environment_label: str) -> str:

    status_emoji = "✅" if summary['unhealthy_instances'] == 0 else "⚠️"
    return (f"{status_emoji} Airflow Health Report [{environment_label}] - "
            f"{summary['healthy_instances']}/{summary['total_instances']} OK "
            f"({summary['health_percentage']}%)")