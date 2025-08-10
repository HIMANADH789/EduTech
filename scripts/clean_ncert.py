#!/usr/bin/env python3
import os
import json
import re
import chardet
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as e:
    raise RuntimeError("PyMuPDF (fitz) is required. Install: pip install pymupdf") from e

RAW_FOLDER = Path("../data/ncert/biology")       # where raw PDFs (or txt) live
CLEAN_FOLDER = Path("../data/clean/biology")    # where JSONs will be saved
CLEAN_FOLDER.mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    # Basic cleaning: collapse multiple newlines and excessive spaces
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n\n', text)           # keep paragraphs but collapse
    text = re.sub(r'[^\S\r\n]{2,}', ' ', text)      # collapse multiple spaces
    text = text.strip()
    return text

def extract_text_from_pdf(pdf_path: Path) -> (str, int):
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        page_text = page.get_text("text")  # plain text extractor
        if page_text:
            text_parts.append(page_text)
    full_text = "\n\n".join(text_parts)
    return full_text, doc.page_count

def read_text_file(path: Path) -> str:
    raw_bytes = path.read_bytes()
    detected = chardet.detect(raw_bytes)
    encoding = detected.get("encoding") or "utf-8"
    return raw_bytes.decode(encoding, errors="ignore")

def looks_like_pdf_bytes(s: str) -> bool:
    # Quick guard: if starts with PDF header or contains 'endstream' etc.
    header = s.lstrip()[:8]
    if header.startswith("%PDF") or "%PDF-" in s[:20]:
        return True
    if "endstream" in s[:200] or "obj" in s[:200]:
        return True
    return False

def make_json_filename(src_name: str, chapter: str):
    safe = "".join(c if c.isalnum() or c in "-._" else "_" for c in src_name)
    return f"{safe}.json"

def process_file(path: Path):
    print(f"Processing: {path}")
    if path.suffix.lower() == ".pdf":
        text, num_pages = extract_text_from_pdf(path)
    elif path.suffix.lower() in {".txt", ".text", ".md"}:
        text = read_text_file(path)
        num_pages = 1
    else:
        print(f"  → Skipping unsupported file type: {path.name}")
        return

    cleaned = clean_text(text)
    if not cleaned:
        print(f"  ❌ Warning: extracted text is empty for {path.name}")
        return

    if looks_like_pdf_bytes(cleaned[:200]):
        print(f"  ❌ Warning: extracted content for {path.name} looks like PDF bytes — skipping. Please check source.")
        return

    # try to derive a chapter id (best-effort fallback)
    chapter_id = path.stem
    out = {
        "source": path.name,
        "chapter": chapter_id,
        "num_pages": num_pages,
        "text": cleaned
    }

    out_filename = make_json_filename(path.stem, chapter_id)
    out_path = CLEAN_FOLDER / out_filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # validate
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if "text" not in loaded or not isinstance(loaded["text"], str):
            print(f"  ❌ Error: JSON saved but missing 'text' key for {out_path}")
        else:
            print(f"  ✓ Saved cleaned JSON: {out_path} (chars: {len(loaded['text'])})")
    except Exception as e:
        print(f"  ❌ Error validating saved JSON: {e}")

def main():
    files = sorted(RAW_FOLDER.iterdir())
    if not files:
        print(f"No files found in {RAW_FOLDER}. Check path.")
        return

    for f in files:
        if f.is_file():
            process_file(f)

if __name__ == "__main__":
    main()
