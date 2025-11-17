from airflow.models import Variable
import logging

from airflow_health.health_checker import check_all_instances, aggregate_health_summary
from airflow_health.email_builder import build_html_report, get_email_subject
from airflow_health.models import AirflowInstance, HealthStatus
from airflow_health.instances_sources import get_instance_source

logger = logging.getLogger(__name__)


def check_instances(env_list: list[str], **context) -> str:
    source_name = Variable.get("instances_source", default_var="from_json_config")
    
    source = get_instance_source(source_name)
    
    airflow_instances = source.get_instances(env_list)
    
    health_statuses = check_all_instances(airflow_instances)

    summary = aggregate_health_summary(health_statuses)

    health_data: Dict[str, Any] = {
        "statuses": [
            {
                "instance": {
                    "team": status.instance.team,
                    "app_code": status.instance.app_code,
                    "environment": status.instance.environment,
                    "release_uid": status.instance.release_uid,
                    "version": status.instance.version,
                },
                "status_code": status.status_code,
                "scheduler_status": status.scheduler_status,
                "dag_processor_status": status.dag_processor_status,
                "triggerer_status": status.triggerer_status,
                "metadatabase_status": status.metadatabase_status,
                "error_message": status.error_message,
            }
            for status in health_statuses
        ],
        "summary": summary,
    }

    context["ti"].xcom_push(key="health_check_data", value=health_data)



def generate_report(env_list: list, **context):
    health_data = context['ti'].xcom_pull(task_ids='check_instances', key='health_check_data')

    health_statuses = []
    for data in health_data['statuses']:
        instance = AirflowInstance(**data['instance'])
        status = HealthStatus(
            instance=instance,
            status_code=data['status_code'],
            scheduler_status=data['scheduler_status'],
            dag_processor_status=data['dag_processor_status'],
            triggerer_status=data['triggerer_status'],
            metadatabase_status=data['metadatabase_status'],
            error_message=data['error_message'],
        )
        health_statuses.append(status)

    summary = health_data['summary']

    html_content = build_html_report(health_statuses, summary, env_list)
    email_subject = get_email_subject(summary, env_list)

    context['ti'].xcom_push(key='html_content', value=html_content)
    context['ti'].xcom_push(key='email_subject', value=email_subject)


def send_report_email(recipients: list, **context):
    html_content = context['ti'].xcom_pull(task_ids='generate_report', key='html_content')
    email_subject = context['ti'].xcom_pull(task_ids='generate_report', key='email_subject')

    print(email_subject)
    #from airflow.operators.email import send_email
    #send_email(
    #    to=recipients,
    #    subject=email_subject,
    #    html_content=html_content,
    #)

