import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

response = requests.get(
  url="https://openrouter.ai/api/v1/auth/key",
  headers={
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
  }
)

print(json.dumps(response.json(), indent=2))

from prompt_utils import create_prompt

print(create_prompt('3K4/8/8/p7/k7/8/8/2q5 b - - 1 52'))