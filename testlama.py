import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama2",
    "prompt": "Explain quantum computing in simple terms."
}

with requests.post(url, json=payload, stream=True) as r:
    for line in r.iter_lines():
        if line:
            data = json.loads(line)
            if "response" in data:
                print(data["response"], end="", flush=True)
