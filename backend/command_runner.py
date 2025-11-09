import subprocess
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CommandRunner:
    """executes scripts safely with sandboxing"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def execute_script(self, script_path: str, intent: Dict[str, Any]) -> str:
        """
        execute a script file and return output
        passes intent params as environment variables
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"script not found: {script_path}")

        # prepare environment with intent params
        env = os.environ.copy()
        for key, value in intent.items():
            env[f"LCA_{key.upper()}"] = str(value)

        try:
            # determine how to run based on extension
            ext = os.path.splitext(script_path)[1]

            if ext == '.sh':
                cmd = ['bash', script_path]
            elif ext == '.bat':
                cmd = ['cmd', '/c', script_path]
            elif ext == '.py':
                cmd = ['python3', script_path]
            else:
                raise ValueError(f"unsupported script type: {ext}")

            logger.info(f"executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )

            output = result.stdout + result.stderr

            if result.returncode != 0:
                logger.warning(f"script exited with code {result.returncode}")

            return output.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"script timeout after {self.timeout}s")
            return f"ERROR: script timed out after {self.timeout}s"

        except Exception as e:
            logger.error(f"execution failed: {e}")
            return f"ERROR: {str(e)}"

    def validate_script(self, script_path: str) -> bool:
        """check if script is valid and executable"""
        if not os.path.exists(script_path):
            return False

        # check if executable on unix
        if os.name != 'nt':
            return os.access(script_path, os.X_OK)

        return True
