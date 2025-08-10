#!/usr/bin/env python3
"""
Process every cleaned JSON in a folder into smaller text chunks and save as one aggregated JSON.
"""

import json
from pathlib import Path
from typing import List, Dict

# ---------- Config ----------
INPUT_FOLDER = Path("../data/clean/biology")   # folder containing your cleaned .json files
OUTPUT_FOLDER = Path("../data/processed")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
AGG_OUTPUT = OUTPUT_FOLDER / "processed_chunks.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SAVE_PER_FILE = False   # if True, also save <source>_chunks.json in OUTPUT_FOLDER
# ----------------------------

def looks_like_pdf_bytes(s: str) -> bool:
    s_strip = s.lstrip()[:30]
    if s_strip.startswith("%PDF") or "endstream" in s[:400] or "obj" in s[:200]:
        return True
    return False

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """
    Chunk by characters but prefer to cut at whitespace to avoid splitting words.
    Returns list of dicts with 'chunk', 'start', 'end'.
    """
    chunks = []
    n = len(text)
    start = 0
    while start < n:
        end = min(start + chunk_size, n)

        # prefer to split at last whitespace inside window to avoid cut words
        if end < n:
            # look for whitespace to the left of end, but not too far left
            r = text.rfind(" ", start, end)
            # only use r if it's not too close to start (to avoid tiny chunks)
            if r and r > start + int(chunk_size * 0.4):
                end = r

        # extract chunk and advance
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"chunk": chunk, "start": start, "end": end})
        # advance start by chunk_size - overlap (but use actual end-start)
        advance = max(1, (end - start) - overlap)
        start = start + advance

    return chunks

def extract_text_from_json(data) -> str:
    """
    Try to locate the most likely text field in the JSON structure.
    - If data is dict and has 'text' -> return it
    - If dict has 'content'/'body'/'chapter_text' prefer these
    - If dict values contain large strings, pick the largest string value
    - If data is list, and items are dicts with 'text', join them
    """
    if isinstance(data, dict):
        # prefer explicit keys
        for key in ("text", "content", "body", "chapter", "chapter_text"):
            if key in data and isinstance(data[key], str) and data[key].strip():
                return data[key].strip()
        # fallback: find largest string value
        largest = ""
        for v in data.values():
            if isinstance(v, str) and len(v) > len(largest):
                largest = v
        return largest.strip()

    if isinstance(data, list):
        # join text fields from list items if present
        texts = []
        for item in data:
            if isinstance(item, dict):
                for key in ("text", "content", "body"):
                    if key in item and isinstance(item[key], str):
                        texts.append(item[key].strip())
                        break
        if texts:
            return "\n\n".join(texts)
        # fallback: if list of strings
        if all(isinstance(i, str) for i in data):
            return "\n\n".join(data)
    return ""

def process_file(filepath: Path, global_chunks: List[Dict]):
    try:
        raw = json.loads(filepath.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:
        print(f"❌ Failed to load JSON {filepath.name}: {e}")
        return

    # if it's already a per-file chunk list format, detect and append directly
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "chunk" in raw[0]:
        # assume already chunked
        for i, item in enumerate(raw):
            global_chunks.append({
                "id": f"{filepath.stem}_chunk{i}",
                "source": filepath.name,
                "chapter": filepath.stem,
                "chunk_index": i,
                "char_start": item.get("start"),
                "char_end": item.get("end"),
                "text": item.get("chunk") if "chunk" in item else item.get("text", "")
            })
        print(f"  (already chunked) added {len(raw)} chunks from {filepath.name}")
        return

    # otherwise, extract text
    text = extract_text_from_json(raw)
    if not text:
        print(f"❌ No text found in {filepath.name} — skipping")
        return

    # guard: ensure we didn't accidentally capture PDF bytes
    if looks_like_pdf_bytes(text[:400]):
        print(f"❌ Detected PDF-like bytes inside JSON {filepath.name} — skip and re-generate real text JSON")
        return

    # chunk the text
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunks:
        print(f"⚠️  No chunks created for {filepath.name} (text too short?) — saving as single chunk")
        chunks = [{"chunk": text, "start": 0, "end": len(text)}]

    # append to global list with metadata
    for i, c in enumerate(chunks):
        global_chunks.append({
            "id": f"{filepath.stem}_chunk{i}",
            "source": filepath.name,
            "chapter": raw.get("chapter", filepath.stem if isinstance(raw, dict) else filepath.stem),
            "chunk_index": i,
            "char_start": c.get("start"),
            "char_end": c.get("end"),
            "text": c.get("chunk")
        })

    # optional: save per-file chunked JSON
    if SAVE_PER_FILE:
        out_file = OUTPUT_FOLDER / f"{filepath.stem}_chunks.json"
        out_list = [
            {
                "id": f"{filepath.stem}_chunk{i}",
                "chunk_index": i,
                "start": c["start"],
                "end": c["end"],
                "chunk": c["chunk"]
            } for i, c in enumerate(chunks)
        ]
        out_file.write_text(json.dumps(out_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved per-file chunks: {out_file.name}")

    print(f"  ✓ Processed {filepath.name}: created {len(chunks)} chunks")

def main():
    files = sorted([p for p in INPUT_FOLDER.iterdir() if p.is_file() and p.suffix.lower() == ".json"])
    if not files:
        print(f"No JSON files found in {INPUT_FOLDER}.")
        return

    all_chunks = []
    for f in files:
        print(f"Processing file: {f.name}")
        process_file(f, all_chunks)

    # write aggregated output
    AGG_OUTPUT.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Aggregated {len(all_chunks)} chunks written to: {AGG_OUTPUT}")

    # print a quick preview
    preview_n = min(3, len(all_chunks))
    print("\nPreview:")
    for i in range(preview_n):
        entry = all_chunks[i]
        print(f"- [{entry['id']}] source={entry['source']} chars={len(entry['text'])}")
        print(entry['text'][:300].replace("\n", " ") + ("..." if len(entry['text'])>300 else ""))
        print()

if __name__ == "__main__":
    main()
