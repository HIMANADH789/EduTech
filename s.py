# import json
# import os

# CLEAN_FOLDER = "data/clean/biology"

# # Pick the first JSON file in the folder
# sample_file = sorted(os.listdir(CLEAN_FOLDER))[0]
# with open(os.path.join(CLEAN_FOLDER, sample_file), "r") as f:
#     data = json.load(f)

# print(json.dumps(data, indent=2))
import os, json

for file in os.listdir("data/clean/biology"):
    path = os.path.join("data/clean/biology", file)
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        print(f"❌ {file} is not valid JSON: {e}")
