import requests
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AirflowInstance:
    team: str
    app_code: str
    environment: str
    release_uid: str
    version: str
    
    @property
    def url(self) -> str:
        return f"wwwwwwwwwwwwwwwwwwwwwwwwwwww"
    
    @property
    def health_url(self) -> str:
        return "http://ccccccccccccc:8080/api/v1/health"  #f"{self.url}/api/v1/health"


@dataclass
class HealthStatus:
    instance: AirflowInstance
    status_code: int
    scheduler_status: str = "N/A"
    dag_processor_status: str = "N/A"
    triggerer_status: str = "N/A"
    metadatabase_status: str = "N/A"
    error_message: str = None
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()
    
    @property
    def is_healthy(self) -> bool:
        return self.status_code == 200


