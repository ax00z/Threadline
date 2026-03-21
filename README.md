# Threadline

Network analysis and timeline reconstruction for seized communication datasets.

Built for investigators dealing with WhatsApp, Telegram, and SMS exports from forensic extractions. Replaces the spreadsheet workflow.
Drop a file, get a searchable message log, network graph, entity extraction, anomaly detection, and chain-of-custody verification immediately.

---

## What it does

- Parses WhatsApp `.txt` exports, Telegram `.json` exports, and generic CSV from forensic tools
- Builds a searchable message table with per-sender color coding and cross-component filtering
- Network graph with degree, betweenness, closeness centrality, PageRank, and Louvain community detection
- Air-gapped NER: phones, emails, URLs, money, crypto wallets, coordinates, dates, persons, orgs, locations (regex + optional spaCy)
- Anomaly detection: burst activity, off-hours messaging, late-appearing contacts, keyword co-occurrence flagging
- Relationship timeline with per-pair sparklines, duration tracking, and sortable views
- Evidence export: filtered JSONL (chain hashes intact) and full JSON investigation reports
- SHA-256 hash chain of custody — tamper detection on every message, verified on upload
- Standalone Rust verifier binary for independent chain verification
- DuckDB SQL console for ad-hoc queries against the loaded dataset
- Streams files at O(1) memory — a 50k-line export uses ~400KB regardless of file size

---

## Stack

| Layer | Tech |
|---|---|
| Parser / Pipeline | Python 3.11+, FastAPI |
| Graph Engine | NetworkX (centrality, Louvain communities) |
| NLP | regex + spaCy (optional, air-gapped) |
| DB | DuckDB (in-memory analytical queries) |
| UI | SvelteKit 2, Svelte 5 |
| Graph Viz | Sigma.js + Graphology (WebGL) |
| Charts | Chart.js 4 |
| Chain Verification | Python hashlib + Rust standalone binary |

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

## Rust chain verifier

Independently verify the hash chain without trusting the Python pipeline:

```bash
cd rust && cargo build --release
./target/release/threadline-verify exported.jsonl
```

Reads JSONL from stdin or file arg. Recomputes every SHA-256 hash from scratch. Exits 0 if chain is intact, 2 if broken.

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
- [x] Phase 2 — FastAPI backend, SvelteKit dashboard, NetworkX graph, DuckDB store
- [x] Phase 3 — air-gapped NER (10 entity types, regex + optional spaCy)    
- [x] Phase 4 — tactical UI with cross-component selection, graph view, timeline brush
- [x] Phase 5 — SHA-256 hash chain of custody (Python + Rust verifier)
- [x] Phase 6 — anomaly detection, evidence export, relationship timeline
- [x] Phase 7 — profiling and optimizing processing pipeline
- [X] Phase 8 — debug the app end-to-end through the web UI, incorporate ai analysis capabilities
- [] Phase 9 — final debugging and code review, bundle app as portable one click installer
