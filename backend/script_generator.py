import ollama
import os
import logging
import hashlib
from typing import Dict, Any, Optional
import platform

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """generates executable scripts using local LLM"""

    def __init__(self, model: str = "qwen2.5-coder", plugins_dir: str = "../plugins"):
        self.model = model
        self.plugins_dir = os.path.abspath(plugins_dir)
        os.makedirs(self.plugins_dir, exist_ok=True)

        # safety: allowed commands
        self.allowed_commands = {
            'open', 'start', 'osascript', 'say', 'spotify',
            'curl', 'python3', 'node', 'echo', 'caffeinate',
            'pmset', 'brightness', 'shortcuts', 'afplay'
        }

        logger.info(f"script generator initialized with model: {self.model}")

    def generate_script(self, intent: Dict[str, Any]) -> Optional[str]:
        """generate and save a new script based on intent"""
        action = intent.get('action', 'unknown')

        # determine platform
        sys_platform = platform.system()

        if sys_platform == 'Darwin':
            script_type = 'sh'
            shell_cmd = '#!/bin/bash'
        else:
            script_type = 'bat'
            shell_cmd = '@echo off'

        prompt = self._build_prompt(intent, sys_platform)

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.2}
            )

            script_content = self._extract_code(response['response'])

            if not script_content:
                logger.error("failed to extract code from llm response")
                return None

            # validate safety
            if not self._is_safe(script_content):
                logger.warning("generated script failed safety check")
                return None

            # save script
            script_path = self._save_script(action, script_content, script_type)
            logger.info(f"generated script: {script_path}")

            return script_path

        except Exception as e:
            logger.error(f"script generation failed: {e}")
            return None

    def _build_prompt(self, intent: Dict[str, Any], platform: str) -> str:
        """build prompt for code generation"""
        action = intent.get('action', 'unknown')
        params = {k: v for k, v in intent.items() if k != 'action'}

        if platform == 'Darwin':
            platform_name = 'macOS'
            examples = """
Example 1:
Intent: {"action": "open_app", "app": "spotify"}
Script:
#!/bin/bash
open -a "Spotify"

Example 2:
Intent: {"action": "play_music", "playlist": "chill"}
Script:
#!/bin/bash
osascript -e 'tell application "Spotify" to play track "spotify:playlist:37i9dQZF1DX"'
"""
        else:
            platform_name = 'Windows'
            examples = """
Example:
Intent: {"action": "open_app", "app": "chrome"}
Script:
@echo off
start chrome
"""

        prompt = f"""You are a script generator for {platform_name}. Generate a safe, executable script for this intent.

Intent: {intent}
Action: {action}
Parameters: {params}

Requirements:
- Write ONLY the script code, no explanation
- Use only safe commands: {', '.join(self.allowed_commands)}
- Make it executable and reliable
- Handle errors gracefully
- No destructive operations (rm, del, format, etc.)
- Do NOT use sleep or wait commands - keep scripts instant
- Be accurate with app names (Music.app for Apple Music, Spotify.app for Spotify)

{examples}

Now generate the script:"""

        return prompt

    def _extract_code(self, response: str) -> Optional[str]:
        """extract code block from llm response"""
        # try to find code block
        if '```' in response:
            parts = response.split('```')
            for part in parts:
                # skip language identifiers
                lines = part.strip().split('\n')
                if lines and not lines[0].strip() in ['bash', 'sh', 'bat', 'shell']:
                    code = part.strip()
                    if code and (code.startswith('#!') or code.startswith('@')):
                        return code
                elif len(lines) > 1:
                    # language specified, take rest
                    code = '\n'.join(lines[1:]).strip()
                    if code:
                        return code

        # no code blocks, try raw
        response = response.strip()
        if response.startswith('#!/') or response.startswith('@echo'):
            return response

        return None

    def _is_safe(self, script: str) -> bool:
        """check if script only uses allowed commands"""
        dangerous = ['rm ', 'del ', 'format', 'chmod', 'sudo', 'dd ', '>/', 'rf ', 'sleep ']

        script_lower = script.lower()

        for danger in dangerous:
            if danger in script_lower:
                logger.warning(f"unsafe command detected: {danger}")
                return False

        return True

    def _save_script(self, action: str, content: str, ext: str) -> str:
        """save script to plugins directory"""
        # create unique filename
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        filename = f"{action}_{hash_suffix}.{ext}"
        filepath = os.path.join(self.plugins_dir, filename)

        with open(filepath, 'w') as f:
            f.write(content)

        # make executable on unix
        if ext == 'sh':
            os.chmod(filepath, 0o755)

        return filepath
