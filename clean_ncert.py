import os
import json
import re
import chardet  # <-- import chardet

RAW_FOLDER = "data/ncert/cbse_paper"  # Your extracted chapter text files
CLEAN_FOLDER = "data/clean/cbse_paper"

def clean_text(text):
    # Remove extra whitespaces and newlines
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[^\S\r\n]{2,}', ' ', text)
    return text.strip()

def clean_all_chapters():
    os.makedirs(CLEAN_FOLDER, exist_ok=True)
    for filename in sorted(os.listdir(RAW_FOLDER)):
        if filename.startswith("Science"):
            chapter_number = filename[6:11]
            filepath = os.path.join(RAW_FOLDER, filename)

            # Detect encoding with chardet
            with open(filepath, 'rb') as f:
                raw_bytes = f.read()
                detected = chardet.detect(raw_bytes)
                encoding = detected['encoding'] if detected['encoding'] else 'utf-8'

            # Open file with detected encoding
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                raw_text = f.read()

            cleaned_text = clean_text(raw_text)
            output = {
                "chapter": chapter_number,
                "text": cleaned_text
            }

            out_file = os.path.join(CLEAN_FOLDER, f"Science_{chapter_number}.json")
            with open(out_file, "w", encoding="utf-8") as out:
                json.dump(output, out, indent=2, ensure_ascii=False)
            print(f"[✓] Saved cleaned chapter {chapter_number}")

if __name__ == "__main__":
    clean_all_chapters()
