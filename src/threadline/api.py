from __future__ import annotations
import json
import tempfile
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from threadline.parser import parse_file, detect_format

app = FastAPI(title="Threadline")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ACCEPTED = {".txt", ".json", ".csv"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename or ""
    ext = Path(name).suffix.lower()
    if ext not in _ACCEPTED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Send .txt, .json, or .csv")

    suffix = ext if ext else ".txt"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        messages = []
        sender_counts: Counter[str] = Counter()
        for msg in parse_file(tmp_path):
            d = msg.to_dict()
            messages.append(d)
            sender_counts[msg.sender] += 1

        if not messages:
            raise HTTPException(422, "No messages found in file")

        stats = {
            "total_messages": len(messages),
            "unique_senders": len(sender_counts),
            "senders": dict(sender_counts.most_common()),
            "first_message": messages[0]["timestamp"],
            "last_message": messages[-1]["timestamp"],
            "source_format": detect_format(tmp_path),
        }
        return {"messages": messages, "stats": stats}
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("threadline.api:app", host="0.0.0.0", port=8000, reload=True)
