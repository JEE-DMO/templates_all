DAG_CONFIG = {
    "airflow_health_check_prod": {
        "description": "Health check from PROD (prod, pprd)",
        "env_list": ["prod", "pprd"],
        "schedule_interval": "0 */6 * * *",
        "tags": ["airflow", "monitoring", "prod"],
    },
    "airflow_health_check_hprod": {
        "description": "Health check for HPROD (dev, int, qual)",
        "env_list": ["dev", "int", "qual"],
        "schedule_interval": "0 */6 * * *",
        "tags": ["airflow", "monitoring", "hprod"],
    },
}

for dag_id, cfg in DAG_CONFIG.items():
    with DAG(
        dag_id=dag_id,
        default_args={
            'owner': 'data-platform',
            'depends_on_past': False,
            'email_on_failure': True,
        },
        description=cfg['description'],
        schedule_interval=cfg['schedule_interval'],
        start_date=datetime(2025, 11, 13),
        catchup=False,
        tags=cfg["tags"]
    ) as dag:
        

        task_check_instances = PythonOperator(
            task_id='check_instances',
            python_callable=check_instances,
            op_kwargs={'env_list': cfg['env_list']},
        )

        task_generate_report = PythonOperator(
            task_id='generate_report',
            python_callable=generate_report,
            op_kwargs={'env_list': cfg['env_list']}
        )

        task_send_email = PythonOperator(
            task_id='send_email',
            python_callable=send_report_email,
        )

        task_check_instances >> task_generate_report >> task_send_email
        
        globals()[dag_id] = dag 
