# import requests
# import json

# url = "http://localhost:11434/api/generate"
# payload = {
#     "model": "llama2",
#     "prompt": "Explain quantum computing in simple terms."
# }

# with requests.post(url, json=payload, stream=True) as r:
#     for line in r.iter_lines():
#         if line:
#             data = json.loads(line)
#             if "response" in data:
#                 print(data["response"], end="", flush=True)
import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama2",   # or "mistral"
    "prompt": "Explain quantum computing in simple terms.",
    "stream": True
}

r = requests.post(url, json=payload)

print("Status code:", r.status_code)

if r.status_code != 200:
    print("Error response:", r.text)
    exit(1)

for line in r.iter_lines():
    if line:
        data = json.loads(line)
        if "error" in data:
            print("\nERROR:", data["error"])
            break
        if "response" in data:
            print(data["response"], end="", flush=True)
