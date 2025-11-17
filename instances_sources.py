from abc import ABC, abstractmethod
from typing import List
from airflow.models import Variable
import re, random
from airflow_health.models import AirflowInstance
import logging

logger = logging.getLogger(__name__)

class InstanceSource(ABC):
    @abstractmethod
    def get_instances(self, env_list: List[str]) -> List[AirflowInstance]:
        pass


class FromAirflowCtlResult(InstanceSource):
    def get_instances(self, env_list: List[str]) -> List[AirflowInstance]:
        raw_text = Variable.get("airflowctl_inst_list_result", default_var="").strip()
        lines = raw_text.splitlines()

        logger.info(f"📥 Parsing {len(lines)} lines from airflowctl result")
        logger.debug(f"Raw content:\n{raw_text}")

        instances = []
        for line in lines:
            match = re.search(
                r"^\d+:\s+[^-\s]+-"
                r"(?P<app>ap\d+)-"
                r"(?P<env>\w+)-"
                r"(?P<uid>[A-Za-z0-9]{8})"
                r"(?:\s+\([^)]+\))?"
                r"(?:\s+\[(?P<ver>[^\]]+)\])?",
                line.strip()
            )

            if match:
                inst = AirflowInstance(
                    team=random.choice(["bcef", "pf", "arval", "cardif", "fortis"]),
                    app_code=match.group("app"),
                    environment=match.group("env"),
                    release_uid=match.group("uid"),
                    version=match.group("ver") or "X.Z.Z"
                )
                if inst.environment in env_list:
                    instances.append(inst)
                else:
                    logger.debug(f"Ignored (env not in list): {line}")
            else:
                logger.warning(f"⚠️ Ligne ignorée (format non reconnu) : {line}")

        logger.info(f"✅ {len(instances)} instances retenues après filtre")
        return instances

class FromAirflowCtlCmd(InstanceSource):
    def get_instances(self, env_list: List[str]) -> List[AirflowInstance]:
        get_running_instances
        return []


class FromJsonConfig(InstanceSource):
    def get_instances(self, env_list: List[str]) -> List[AirflowInstance]:
        instances_json = Variable.get("project_config", deserialize_json=True)
        #raw_json = Variable.get("airflow_instances_json_config", default_var="{}")
        #data = json.loads(raw_json)

        instances: List[AirflowInstance] = []

        for team, envs in instances_json.items():
            for env, items in envs.items():
                if env not in env_list:
                    continue

                for item in items:
                    instances.append(AirflowInstance(
                        team = team,
                        app_code = item.get("APP_CODE", ""),
                        environment = item.get("ENV", env),
                        release_uid = item.get("RELEASE_UUID", ""),
                        version = item.get("VERSION", "unknown"),
                    ))

        return instances

class FromPmsApi(InstanceSource):
    def get_instances(self, env_list: List[str]) -> List[AirflowInstance]:
        # TODO: appeler une API, parser les réponses
        return []


def get_instance_source(source_name: str) -> InstanceSource:
    
    mapping = {
        "from_airflowctl_cmd": FromAirflowCtlCmd,
        "from_airflowctl_result": FromAirflowCtlResult,
        "from_json_config": FromJsonConfig,
        "from_pms_api": FromPmsApi,
    }

    try:
        return mapping[source_name]()
    except KeyError:
        raise ValueError(f"❌ Source inconnue dans 'instances_source': {source_name}")



