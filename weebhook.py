import requests
import json
from airflow.operators.python import PythonOperator
from airflow import DAG
from datetime import datetime

def send_health_summary_to_teams(**context):
    summary = context['ti'].xcom_pull(task_ids='generate_summary')

    webhook_url = "https://outlook.office.com/webhook/..."  # Ton webhook Teams ici

    # Construction de l'Adaptive Card
    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Large",
                            "weight": "Bolder",
                            "text": "✅ Health Check Summary",
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Total Instances:", "value": str(summary['total_instances'])},
                                {"title": "Healthy Instances:", "value": str(summary['healthy_instances'])},
                                {"title": "Unhealthy Instances:", "value": str(summary['unhealthy_instances'])},
                                {"title": "Checked At:", "value": summary['checked_at']},
                            ]
                        },
                        {
                            "type": "TextBlock",
                            "text": "**By Environment**",
                            "weight": "Bolder",
                            "wrap": True
                        },
                        *[
                            {
                                "type": "TextBlock",
                                "text": f"- {env}: {env_data['healthy']}/{env_data['total']} healthy",
                                "wrap": True
                            }
                            for env, env_data in summary['by_environment'].items()
                        ],
                        {
                            "type": "TextBlock",
                            "text": "**By Business Line**",
                            "weight": "Bolder",
                            "wrap": True
                        },
                        *[
                            {
                                "type": "TextBlock",
                                "text": f"- {bl}: {bl_data['healthy']}/{bl_data['total']} healthy",
                                "wrap": True
                            }
                            for bl, bl_data in summary['by_business_line'].items()
                        ]
                    ]
                }
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, data=json.dumps(card), headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Request to Teams returned an error {response.status_code}, response: {response.text}")

# DAG & task
with DAG(
    dag_id='health_check_notification',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False
) as dag:

    generate_summary = PythonOperator(
        task_id='generate_summary',
        python_callable=aggregate_health_summary,  # Ton callable ici
        provide_context=True
    )

    send_to_teams = PythonOperator(
        task_id='send_to_teams',
        python_callable=send_health_summary_to_teams,
        provide_context=True
    )

    generate_summary >> send_to_teams
