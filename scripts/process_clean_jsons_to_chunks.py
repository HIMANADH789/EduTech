#!/usr/bin/env python3
"""
Process every cleaned JSON in a folder into smaller text chunks
and save as one aggregated JSON.
"""

import json
from pathlib import Path
from typing import List, Dict

# ============================================================
# 🔒 PATH CONFIG — SAFE, ROOTED, NO RELATIVE HELL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent  # C:\EduTec

INPUT_FOLDER = BASE_DIR / "data" / "clean" / "biology"
OUTPUT_FOLDER = BASE_DIR / "data" / "processed"
AGG_OUTPUT = OUTPUT_FOLDER / "processed_chunks.json"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SAVE_PER_FILE = False

# ============================================================

def looks_like_pdf_bytes(s: str) -> bool:
    s_strip = s.lstrip()[:30]
    return (
        s_strip.startswith("%PDF")
        or "endstream" in s[:400]
        or " obj" in s[:200]
    )

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Dict]:

    chunks = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)

        if end < n:
            r = text.rfind(" ", start, end)
            if r != -1 and r > start + int(chunk_size * 0.4):
                end = r

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "chunk": chunk,
                "start": start,
                "end": end
            })

        advance = max(1, (end - start) - overlap)
        start += advance

    return chunks

def extract_text_from_json(data) -> str:
    if isinstance(data, dict):
        for key in ("text", "content", "body", "chapter", "chapter_text"):
            if key in data and isinstance(data[key], str) and data[key].strip():
                return data[key].strip()

        largest = ""
        for v in data.values():
            if isinstance(v, str) and len(v) > len(largest):
                largest = v
        return largest.strip()

    if isinstance(data, list):
        texts = []
        for item in data:
            if isinstance(item, dict):
                for key in ("text", "content", "body"):
                    if key in item and isinstance(item[key], str):
                        texts.append(item[key].strip())
                        break
        if texts:
            return "\n\n".join(texts)

        if all(isinstance(i, str) for i in data):
            return "\n\n".join(data)

    return ""

def process_file(filepath: Path, global_chunks: List[Dict]):
    try:
        raw = json.loads(filepath.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:
        print(f"❌ Failed to load {filepath.name}: {e}")
        return

    # Already chunked format
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "chunk" in raw[0]:
        for i, item in enumerate(raw):
            global_chunks.append({
                "id": f"{filepath.stem}_chunk{i}",
                "source": filepath.name,
                "chapter": filepath.stem,
                "chunk_index": i,
                "char_start": item.get("start"),
                "char_end": item.get("end"),
                "text": item.get("chunk", "")
            })
        print(f"✓ {filepath.name}: reused {len(raw)} existing chunks")
        return

    text = extract_text_from_json(raw)
    if not text:
        print(f"⚠️  No text found in {filepath.name}, skipped")
        return

    if looks_like_pdf_bytes(text):
        print(f"❌ PDF-like binary detected in {filepath.name}, skipped")
        return

    chunks = chunk_text(text)
    if not chunks:
        chunks = [{"chunk": text, "start": 0, "end": len(text)}]

    chapter_name = (
        raw.get("chapter", filepath.stem)
        if isinstance(raw, dict)
        else filepath.stem
    )

    for i, c in enumerate(chunks):
        global_chunks.append({
            "id": f"{filepath.stem}_chunk{i}",
            "source": filepath.name,
            "chapter": chapter_name,
            "chunk_index": i,
            "char_start": c["start"],
            "char_end": c["end"],
            "text": c["chunk"]
        })

    print(f"✓ {filepath.name}: {len(chunks)} chunks created")

def main():
    if not INPUT_FOLDER.exists():
        raise FileNotFoundError(f"Input folder not found: {INPUT_FOLDER}")

    files = sorted(
        p for p in INPUT_FOLDER.iterdir()
        if p.is_file() and p.suffix.lower() == ".json"
    )

    if not files:
        print(f"No JSON files found in {INPUT_FOLDER}")
        return

    all_chunks = []
    for f in files:
        process_file(f, all_chunks)

    AGG_OUTPUT.write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ SUCCESS")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Saved to: {AGG_OUTPUT}")

    for entry in all_chunks[:3]:
        print(f"\n[{entry['id']}] {entry['source']}")
        print(entry["text"][:300].replace("\n", " ") + "...")

if __name__ == "__main__":
    main()
