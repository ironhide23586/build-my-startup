import os
import requests
from openai import OpenAI

class OfflineAIAdapter:
    def __init__(self):
        self.offline_model_url = os.getenv('OFFLINE_MODEL_URL', 'http://localhost:11434')
        self.offline_model_name = os.getenv('OFFLINE_MODEL_NAME', 'text-davinci-002')
        self.openai_api = OpenAI(os.getenv('OPENAI_API_KEY'))
    
    def query(self, prompt):
        try:
            # Try querying the local model
            response = requests.post(
                f'{self.offline_model_url}/v1/engines/{self.offline_model_name}/completions',
                json={'prompt': prompt, 'max_tokens': 60}
            )
            response.raise_for_status()
        except (requests.exceptions.RequestException, ValueError):
            # If an error occurs, fallback to OpenAI
            print("Local model unavailable, falling back to OpenAI...")
            response = self.openai_api.Completion.create(
                engine="davinci-codex",
                prompt=prompt,
                max_tokens=60
            )
        return response.json()['choices'][0]['text']
from offline_ai_adapter import OfflineAIAdapter

class AIAgent:
    def __init__(self):
        self.ai = OfflineAIAdapter()

    def get_response(self, prompt):
        return self.ai.query(prompt)