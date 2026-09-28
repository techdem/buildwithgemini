import json
import logging
import os
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

logger = logging.getLogger(__name__)

def get_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Loads sandbox_resource_name or remote_agent_runtime_id from deployment_metadata.json and initializes AgentEngineSandboxCodeExecutor."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_path = os.path.join(project_dir, "deployment_metadata.json")

    sandbox_id = None
    agent_engine_id = None

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                meta = json.load(f)
                sandbox_id = meta.get("sandbox_resource_name")
                agent_engine_id = meta.get("remote_agent_runtime_id")
        except Exception as e:
            logger.warning(f"Could not read deployment_metadata.json: {e}")

    logger.info(f"Initializing AgentEngineSandboxCodeExecutor with sandbox_id={sandbox_id}, agent_engine_id={agent_engine_id}")

    return AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_id,
        agent_engine_resource_name=agent_engine_id if not sandbox_id else None
    )
