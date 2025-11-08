import ollama
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NLUService:
    """handles natural language understanding using local ollama model"""

    def __init__(self, model: str = "phi3"):
        self.model = model
        self._check_model()

    def _check_model(self):
        """verify ollama model is available"""
        try:
            ollama.list()
            logger.info(f"ollama connected, using model: {self.model}")
        except Exception as e:
            logger.warning(f"ollama not ready: {e}")

    def parse_intent(self, query: str) -> Dict[str, Any]:
        """
        parse natural language into structured intent
        returns dict like: {"action": "open_music", "playlist": "morning_vibes"}
        """
        prompt = f"""You are a command parser. Convert this natural language command into a JSON intent.

Rules:
- Extract the main action (e.g., open, play, create, search, control)
- Extract relevant parameters (e.g., app names, playlist names, file paths)
- Return ONLY valid JSON, no explanation
- Use snake_case for keys

Examples:
Input: "play my morning playlist"
Output: {{"action": "play_music", "playlist": "morning"}}

Input: "open chrome"
Output: {{"action": "open_app", "app": "chrome"}}

Input: "create a new note"
Output: {{"action": "create_note"}}

Now parse this command:
Input: "{query}"
Output:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.1}
            )

            # extract json from response
            text = response['response'].strip()

            # try to find json in response
            start = text.find('{')
            end = text.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = text[start:end]
                intent = json.loads(json_str)
                return intent
            else:
                # fallback
                return {"action": "unknown", "query": query}

        except Exception as e:
            logger.error(f"intent parsing failed: {e}")
            # fallback intent
            return {"action": "unknown", "query": query}

    def extract_keywords(self, text: str) -> list:
        """extract key terms for embedding search"""
        # simple keyword extraction
        # could be improved with proper nlp
        words = text.lower().split()
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'my'}
        return [w for w in words if w not in stopwords and len(w) > 2]
