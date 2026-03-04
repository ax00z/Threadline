# Threadline

Network analysis and timeline reconstruction for seized communication datasets.

Built for investigators dealing with WhatsApp, Telegram, and SMS exports from forensic extractions. Replaces the spreadsheet workflow. 
Drop a file, get a searchable message log, participant breakdown, and activity timeline immediately.

---

## What it does

- Parses WhatsApp `.txt` exports, Telegram `.json` exports, and generic CSV from forensic tools
- Builds a searchable message table with per-sender color coding
- Shows participant message counts and a daily activity timeline
- Streams files at O(1) memory. A 50k-line export uses around 400KB regardless of file size
- Network graph (Phase 2, coming)
- Air-gapped NLP entity extraction (Phase 3, coming)

---

## Stack

| Layer | Tech |
|---|---|
| Parser / API | Python 3.11+, FastAPI |
| UI | SvelteKit 2, Svelte 5 |
| Charts | Chart.js 4 |
| Graph (Phase 2) | Sigma.js + Graphology |
| DB (Phase 2) | DuckDB |
| Crypto chain (Phase 5) | Rust |

---

## Supported formats

| Format | Extension | Source |
|---|---|---|
| WhatsApp export | `.txt` | Settings → Chats → Export |
| Telegram export | `.json` | Telegram Desktop → Export |
| Generic CSV | `.csv` | Cellebrite, UFED, custom forensic tools |

CSV column names are auto-detected. It looks for variants of `timestamp`, `sender`, `body` — case-insensitive, handles common forensic tool column naming.

---

## Setup

**Requirements:** Python 3.11+, Node 18+

```bash
# backend
pip install -e ".[dev]"

# frontend
cd web && npm install
```

**Run dev servers:**

```bash
# terminal 1 — API on :8000
python -m threadline.api

# terminal 2 — UI on :5173
cd web && npm run dev
```

Open `http://localhost:5173` and drop a file.

---

## CLI

```bash
# parse to JSONL
python -m threadline parse evidence/chat.txt -o out.jsonl --stats

# Telegram export
python -m threadline parse export.json --stats

# CSV
python -m threadline parse sms_dump.csv --stats
```

---

## Tests

```bash
pytest tests/ -v
```

Generate synthetic test data:

```bash
# WhatsApp format
python scripts/gen_test_data.py -n 10000 -p 8 --format whatsapp -o data/test.txt

# Telegram format
python scripts/gen_test_data.py -n 5000 -p 4 --format telegram -o data/test.json
```

## Roadmap

- [x] Phase 1 — streaming parser, CLI, tests
- [x] Phase 2 (partial) — FastAPI backend, SvelteKit dashboard
- [ ] Phase 2 — NetworkX graph engine, centrality metrics
- [ ] Phase 3 — air-gapped spaCy NER (phones, locations, names)
- [ ] Phase 4 — full tactical UI with graph view
- [ ] Phase 5 — Rust cryptographic chain of custody (SHA-256 Merkle)
