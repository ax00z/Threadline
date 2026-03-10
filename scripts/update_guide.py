"""Update STUDY_GUIDE.md with NER and DuckDB sections."""
import os

GUIDE_PATH = os.path.expanduser(r"~\Desktop\STUDY_GUIDE.md")

with open(GUIDE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# === 1. Update Table of Contents ===
content = content.replace(
    """1. What Threadline Actually Is
2. Architecture Overview
3. Phase 1 -- The Streaming Parser
4. Phase 2 -- The Graph Engine (+ Community Detection & PageRank)
5. The REST API (FastAPI)
6. The Frontend (SvelteKit + Sigma.js)
7. Testing Strategy
8. Core CS Concepts You Can Talk About
9. Hands-On Practice Exercises
10. What to Work On Next
11. Interview Talking Points""",
    """1. What Threadline Actually Is
2. Architecture Overview
3. Phase 1 -- The Streaming Parser
4. Phase 2 -- The Graph Engine (+ Community Detection & PageRank)
5. Phase 3 -- Named Entity Recognition (Regex NER)
6. DuckDB -- Embedded Analytical Database
7. The REST API (FastAPI)
8. The Frontend (SvelteKit + Sigma.js)
9. Testing Strategy
10. Core CS Concepts You Can Talk About
11. Hands-On Practice Exercises
12. What to Work On Next
13. Interview Talking Points"""
)

# === 2. Insert NER + DuckDB sections before REST API ===
NER_SECTION = r"""

## 5. Phase 3 -- Named Entity Recognition (Regex NER)

**File**: src/threadline/ner.py

### 5.1 What NER Does

Named Entity Recognition (NER) automatically finds "interesting things" in text -- phone numbers, emails, URLs, money amounts, crypto wallets, coordinates, dates. In forensic analysis, these are the gold nuggets buried in thousands of messages.

**Why regex instead of spaCy/ML?**
- **Deterministic**: Same input = same output every time (critical for court evidence)
- **Air-gapped**: No cloud API calls, no model downloads, zero dependencies
- **Auditable**: A regex pattern can be examined in court; a neural net cannot
- **Fast**: Regex is compiled to a finite state machine, processes text in O(n)

### 5.2 The Entity Types

```python
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_URL, "URL"),              # https://... or www....
    (_EMAIL, "EMAIL"),          # user@domain.tld
    (_CRYPTO, "CRYPTO_WALLET"), # Bitcoin (bc1.../1.../3...) or Ethereum (0x...)
    (_MONEY, "MONEY"),          # $500, EUR 100, 1,234.56 USD
    (_PHONE, "PHONE"),          # (555) 123-4567, +44 20 7946 0958
    (_COORDS, "COORDINATES"),   # 40.7128, -74.0060 (lat/long)
    (_DATE, "DATE"),            # 1/15/2025, Jan 15, 2025
]
```

**Order matters!** URL is checked first because URLs contain dots that could false-match as phone numbers or emails.

### 5.3 Overlap Detection

```python
seen_spans: set[tuple[int, int]] = set()
# Skip if this span overlaps with an already-found entity
if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
    continue
```

This prevents "john@example.com" from matching as both EMAIL and URL. First match wins (priority order in _PATTERNS list).

### 5.4 The Pipeline

```
extract_entities(text)     -> List[Entity] from one message
extract_from_messages(msgs) -> Aggregated results:
  - entities[]            -> Every match with sender + timestamp
  - unique_entities[]     -> Deduplicated, sorted by frequency
  - label_counts{}        -> {"PHONE": 7, "URL": 13, ...}
  - sender_entities{}     -> {"Alice": {"PHONE": ["555-1234"]}}
  - total_found           -> Total entity count
```

### 5.5 Key Patterns In The Code

**Bitcoin address regex**:
```python
r"(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}"  # base58 or bech32
```
- bc1 = SegWit (bech32), 1/3 = legacy/P2SH
- Excludes I, O, l, 0 (base58 omits ambiguous characters)
- 25-39 chars after prefix

**Phone number minimum digit filter**:
```python
if label == "PHONE" and len(re.sub(r"\D", "", match_text)) < 7:
    continue  # Too few digits, likely false positive
```

---

## 6. DuckDB -- Embedded Analytical Database

**File**: src/threadline/store.py

### 6.1 What DuckDB Is

DuckDB is an embedded analytical database -- think "SQLite for analytics". It runs entirely in-memory (no server process), supports full SQL, and is blazing fast for columnar queries.

**Why DuckDB instead of SQLite/Postgres?**
- **In-process**: No separate DB server to manage
- **Columnar storage**: Optimized for analytical queries (GROUP BY, COUNT, aggregations)
- **Zero-copy Python integration**: Shares memory with Python, no serialization overhead
- **Full SQL**: Window functions, CTEs, ILIKE, everything an analyst needs

### 6.2 The MessageStore Class

```python
class MessageStore:
    def __init__(self) -> None:
        self._con = duckdb.connect(":memory:")
        # Creates: messages(row_id, timestamp, sender, body, line_number, source_format)

    def load(self, messages: list[dict]) -> None:
        # DROP + CREATE + INSERT -- fresh table each upload

    def query(self, sql: str, limit: int = 500) -> dict:
        # Safety: only SELECT/WITH/EXPLAIN allowed
        # Auto-adds LIMIT if missing
        # Returns {columns, rows, row_count}
```

### 6.3 Safety Mechanisms

**Read-only enforcement**:
```python
first_word = sql.strip().split()[0].upper()
if first_word not in ("SELECT", "WITH", "EXPLAIN"):
    return {"error": "Only SELECT queries are allowed"}
```

**Auto-LIMIT injection**:
```python
if "LIMIT" not in sql.upper():
    sql = f"SELECT * FROM ({sql}) sub LIMIT {limit}"
```
This prevents accidental full-table dumps on large datasets.

### 6.4 The Query Console (Frontend)

**File**: web/src/lib/components/QueryConsole.svelte

- SQL textarea with syntax-style monospace font
- Ctrl+Enter keyboard shortcut to execute
- 4 preset example queries (quick start for analysts)
- Results table with sticky headers and scroll
- Error display for invalid SQL

**Example queries baked in**:
1. Messages per sender (GROUP BY + COUNT)
2. Keyword search (ILIKE pattern matching)
3. Hourly activity distribution (SUBSTR + GROUP BY)
4. Messages between top 2 participants (subquery + IN)

### 6.5 The API Endpoint

```python
class QueryRequest(BaseModel):
    sql: str

@app.post("/api/query")
async def query(req: QueryRequest):
    result = _store.query(req.sql)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result
```

Pydantic validates the request body. DuckDB errors are caught and returned as 400 responses.

---"""

content = content.replace(
    "## 5. The REST API (FastAPI)",
    NER_SECTION + "\n\n## 7. The REST API (FastAPI)"
)

# === 3. Renumber remaining sections ===
content = content.replace("## 6. The Frontend", "## 8. The Frontend")
content = content.replace("## 7. Testing Strategy", "## 9. Testing Strategy")
content = content.replace("## 8. Core CS Concepts", "## 10. Core CS Concepts")
content = content.replace("## 9. Hands-On Practice", "## 11. Hands-On Practice")
content = content.replace("## 10. What to Work On", "## 12. What to Work On")
content = content.replace("## 11. Interview Talking", "## 13. Interview Talking")

# === 4. Update architecture diagram ===
content = content.replace(
    """|  +-----------------------------------------------+ |
|  | _build_graph()                                 | |
|  |  - degree / betweenness / closeness centrality | |
|  |  - PageRank (eigenvector importance)           | |
|  |  - Louvain community detection                 | |
|  +-----------------------------------------------+ |
+---------------------------------------------------+""",
    """|  +-----------------------------------------------+ |
|  | _build_graph()                                 | |
|  |  - degree / betweenness / closeness centrality | |
|  |  - PageRank (eigenvector importance)           | |
|  |  - Louvain community detection                 | |
|  +-----------------------------------------------+ |
|       |                                             |
|       v                                             |
|  +-----------------------------------------------+ |
|  | ner.py (regex NER)  | store.py (DuckDB)       | |
|  |  PHONE, EMAIL, URL  |  In-memory SQL engine    | |
|  |  MONEY, CRYPTO, GPS |  /api/query endpoint     | |
|  +-----------------------------------------------+ |
+---------------------------------------------------+"""
)

# === 5. Update browser diagram components ===
content = content.replace(
    """|  +----------+ +----------+ +------------------+   |
|  |StatsBar  | |MsgTable  | | CommunityPanel   |   |
|  +----------+ +----------+ +------------------+   |""",
    """|  +----------+ +----------+ +------------------+   |
|  |StatsBar  | |MsgTable  | | CommunityPanel   |   |
|  +----------+ +----------+ +------------------+   |
|  +-----------+ +---------------------------------+  |
|  |EntityPanel| | QueryConsole (DuckDB SQL)       |  |
|  +-----------+ +---------------------------------+  |"""
)

# === 6. Update "Response now includes" ===
content = content.replace(
    """**Response now includes**:
- messages[] -- all parsed messages
- stats{} -- counts, date range, senders
- graph.nodes[] -- each with degree, betweenness, closeness, pagerank, community
- graph.edges[] -- source, target, weight
- graph.communities[] -- id, members, size, total_messages""",
    """**Response now includes**:
- messages[] -- all parsed messages
- stats{} -- counts, date range, senders
- graph.nodes[] -- each with degree, betweenness, closeness, pagerank, community
- graph.edges[] -- source, target, weight
- graph.communities[] -- id, members, size, total_messages
- ner.entities[] -- every extracted entity with sender + timestamp
- ner.unique_entities[] -- deduplicated, sorted by frequency
- ner.label_counts{} -- counts per entity type
- ner.sender_entities{} -- entities grouped by sender

**Additional endpoint**:
- POST /api/query -- Execute DuckDB SQL against loaded messages"""
)

# === 7. Update Components list ===
content = content.replace(
    """- **CommunityPanel [NEW]** -- community members, PageRank rankings, bridge nodes""",
    """- CommunityPanel -- community members, PageRank rankings, bridge nodes
- **EntityPanel [NEW]** -- filterable NER results (chips by type, sender attribution)
- **QueryConsole [NEW]** -- interactive DuckDB SQL editor with preset examples"""
)

# === 8. Update Core CS Concepts ===
content = content.replace(
    """**Generators**: Lazy eval, O(1) memory, yield vs return, iterator protocol
**Graph Theory**: Weighted graphs, centrality (degree/betweenness/closeness), PageRank, Louvain communities, ForceAtlas2
**Regex**: Finite automata, capture groups, state machines
**REST APIs**: Multipart upload, middleware (CORS, GZip), ASGI vs WSGI
**Frontend**: Component arch, reactivity, compiled vs runtime, WebGL vs SVG
**Patterns**: Strategy, generator/iterator, separation of concerns, property testing
**Performance**: O(1) vs O(n), streaming vs buffering, __slots__, WebGL at scale
**Algorithms**: PageRank (Markov chains, eigenvectors), Louvain (modularity optimization, greedy agglomeration)""",
    """**Generators**: Lazy eval, O(1) memory, yield vs return, iterator protocol
**Graph Theory**: Weighted graphs, centrality (degree/betweenness/closeness), PageRank, Louvain communities, ForceAtlas2
**Regex / NER**: Finite automata, capture groups, state machines, entity extraction, overlap resolution, priority ordering
**Databases**: DuckDB (embedded columnar OLAP), in-memory analytics, SQL injection prevention, auto-LIMIT safety
**REST APIs**: Multipart upload, middleware (CORS, GZip), ASGI vs WSGI, Pydantic validation
**Frontend**: Component arch, reactivity (Svelte 5 runes), compiled vs runtime, WebGL vs SVG
**Patterns**: Strategy, generator/iterator, separation of concerns, property testing
**Performance**: O(1) vs O(n), streaming vs buffering, __slots__, WebGL at scale, columnar vs row storage
**Algorithms**: PageRank (Markov chains, eigenvectors), Louvain (modularity optimization, greedy agglomeration)
**Security**: Read-only query enforcement, SQL whitelist validation, temp file cleanup (finally blocks)"""
)

# === 9. Add Exercises 8 and 9 before Exercise 7 ===
EXERCISE_ADDITION = r"""
### Exercise 8: Regex NER Engine (20 min)

```python
# 8a. Test the NER engine directly
from threadline.ner import extract_entities

text = "Call me at (555) 123-4567 or email suspect@darknet.org. Send $500 to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38"
entities = extract_entities(text)
for e in entities:
    print(f"  {e.label:15} {e.text}")

# 8b. Write your OWN regex for IP addresses:
import re
_IP = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
test = "Server at 192.168.1.100 responded to 10.0.0.1"
print([m.group() for m in _IP.finditer(test)])

# 8c. Challenge: Why does Threadline check URL before EMAIL?
# Try: "Visit https://user@example.com/path"
# What happens if EMAIL is checked first?

# 8d. Read src/threadline/ner.py lines 93-117.
# Trace through extract_entities() with this input:
# "Meet at 40.7128, -74.0060 on 3/15/2026"
# Which entities are found? In what order?
```

**What to explain**: "I built a zero-dependency regex NER engine for forensic analysis. It extracts 7 entity types with priority-based overlap resolution. Regex over ML because forensic tools need deterministic, auditable results."

### Exercise 9: DuckDB SQL Analytics (20 min)

```python
# 9a. Start the API and upload a file, then use curl:
# curl -X POST http://127.0.0.1:8000/api/query \
#   -H "Content-Type: application/json" \
#   -d '{"sql": "SELECT sender, COUNT(*) as n FROM messages GROUP BY sender ORDER BY n DESC"}'

# 9b. Try these queries in the QueryConsole:

# Find messages containing specific keywords:
# SELECT timestamp, sender, body FROM messages
# WHERE body ILIKE '%money%' OR body ILIKE '%transfer%'

# Hourly message distribution:
# SELECT SUBSTR(timestamp, 12, 2) as hour, COUNT(*) as msgs
# FROM messages GROUP BY hour ORDER BY hour

# Window function -- running total per sender:
# SELECT sender, timestamp,
#   COUNT(*) OVER (PARTITION BY sender ORDER BY timestamp) as running_total
# FROM messages

# 9c. Try an invalid query and see the error handling:
# DELETE FROM messages  -- should return "Only SELECT queries allowed"
# SELECT * FROM nonexistent  -- should return DuckDB error

# 9d. Read src/threadline/store.py
# Find: Where is auto-LIMIT injected? Why wrap in subquery?
# What happens if someone tries "SELECT * FROM messages; DROP TABLE messages"?
```

**What to explain**: "I embedded DuckDB for ad-hoc SQL analytics over parsed messages. It's columnar (fast for aggregations), in-process (no server), and I enforce read-only access with SQL keyword whitelisting and auto-LIMIT injection."

"""

content = content.replace(
    "### Exercise 7: Read The Code Challenge (30 min)",
    EXERCISE_ADDITION + "### Exercise 10: Read The Code Challenge (30 min)"
)

# === 10. Update "What to Work On Next" ===
content = content.replace(
    """### DONE
- [x] A. Community Detection (Louvain)
- [x] B. PageRank

### HIGH PRIORITY -- Build Next
- [ ] C. spaCy NER (Phase 3) -- 4-6 hours
- [ ] D. DuckDB -- 3-4 hours

### MEDIUM PRIORITY
- [ ] E. Temporal Graph -- 6-8 hours
- [ ] F. Export (GEXF, PNG, PDF) -- 4-6 hours
- [ ] G. Keyword Heatmap -- 2-3 hours
- [ ] H. Sentiment Analysis -- 3-4 hours

### LOWER PRIORITY
- [ ] I. Rust Crypto Chain -- 2-3 days
- [ ] J. Anomaly Detection -- 4-5 hours
- [ ] K. Multi-Chat Merge -- 3-4 hours""",
    """### DONE
- [x] A. Community Detection (Louvain)
- [x] B. PageRank
- [x] C. Named Entity Recognition (Regex NER -- 7 entity types)
- [x] D. DuckDB (embedded SQL query console)

### HIGH PRIORITY -- Build Next
- [ ] E. Temporal Graph (time-slider, evolving communities) -- 6-8 hours
- [ ] F. Export (GEXF, PNG, PDF report) -- 4-6 hours
- [ ] G. Keyword Heatmap (sender x keyword matrix) -- 2-3 hours

### MEDIUM PRIORITY
- [ ] H. Sentiment Analysis -- 3-4 hours
- [ ] I. Anomaly Detection (burst patterns, unusual hours) -- 4-5 hours
- [ ] J. Multi-Chat Merge (combine multiple exports) -- 3-4 hours

### LOWER PRIORITY
- [ ] K. Rust Crypto Chain (SHA-256 Merkle tree) -- 2-3 days
- [ ] L. Advanced NER (custom patterns, entity linking) -- 3-4 hours"""
)

# === 11. Update interview "Tell me about a project" ===
content = content.replace(
    '''"I built Threadline, a forensic analysis platform for law enforcement. It parses WhatsApp/Telegram/CSV exports into interactive network graphs. The backend streams at 35k msg/s with O(1) memory using Python generators. The graph engine computes degree, betweenness, closeness centrality plus PageRank and Louvain community detection. The frontend uses SvelteKit with Sigma.js WebGL rendering. Nodes are colored by automatically detected communities, and a panel highlights cross-community bridge nodes -- the people connecting separate groups."''',
    '''"I built Threadline, a forensic analysis platform for law enforcement. It parses WhatsApp/Telegram/CSV exports into interactive network graphs. The backend streams at 35k msg/s with O(1) memory using Python generators. The graph engine computes centrality metrics, PageRank, and Louvain community detection. I built a regex-based NER engine that extracts phones, emails, crypto wallets, and more -- deterministic and auditable for court use. There's an embedded DuckDB SQL console for ad-hoc analytics. The frontend uses SvelteKit with Sigma.js WebGL rendering, community-colored nodes, and filterable entity panels."'''
)

# === 12. Add new interview Q&As ===
content = content.replace(
    '### "Testing?"',
    '''### "Why regex NER instead of a ML model?"

"Forensic tools need deterministic, reproducible results -- the same file must produce the exact same output every time. ML models have variance between runs and versions. My regex engine is also fully auditable: you can examine the exact pattern that matched in court. Plus it's air-gapped with zero dependencies, which matters when analyzing seized device data on restricted networks."

### "How does the SQL console work?"

"I embedded DuckDB as an in-memory analytical database. When a file is uploaded, messages are bulk-inserted into a columnar table. The /api/query endpoint accepts SQL, validates it's read-only using keyword whitelisting, auto-injects LIMIT to prevent full-table dumps, and returns results as JSON. The frontend has a QueryConsole component with preset examples and Ctrl+Enter execution."

### "Testing?"'''
)

# === 13. Update test info ===
content = content.replace(
    """### 14 Unit Tests
WhatsApp bracket/dash, 24h time, multi-line, system filtering, Telegram JSON, CSV, auto-detection, serialization.""",
    """### 15 Unit Tests
WhatsApp bracket/dash, 24h time, multi-line, system filtering, Telegram JSON, CSV, auto-detection, serialization.

### NER Verification
80 entities extracted from test data: PHONE (7), URL (13), MONEY (20), EMAIL (13), COORDINATES (7), DATE (13), CRYPTO_WALLET (7). Overlap resolution working -- no double-matches.

### DuckDB Verification
Query console tested: GROUP BY aggregation returns correct per-sender counts. Read-only enforcement blocks DELETE/UPDATE. Auto-LIMIT prevents unbounded results."""
)

# === 14. Update Quick Reference ===
content = content.replace(
    """# Quick graph test in Python shell
from threadline.parser import parse_file
from threadline.api import _build_graph
msgs = [m.to_dict() for m in parse_file("data/test_communities.txt")]
g = _build_graph(msgs)
print(f"{len(g['communities'])} communities, {len(g['nodes'])} nodes")
```""",
    """# Quick graph test in Python shell
from threadline.parser import parse_file
from threadline.api import _build_graph
msgs = [m.to_dict() for m in parse_file("data/test_communities.txt")]
g = _build_graph(msgs)
print(f"{len(g['communities'])} communities, {len(g['nodes'])} nodes")

# Quick NER test
from threadline.ner import extract_entities
ents = extract_entities("Call (555) 123-4567 or email me@test.com")
for e in ents:
    print(f"  {e.label}: {e.text}")

# Quick DuckDB test (after uploading a file)
import requests
r = requests.post("http://127.0.0.1:8000/api/query",
    json={"sql": "SELECT sender, COUNT(*) FROM messages GROUP BY sender"})
print(r.json())
```"""
)

# === 15. Update last-updated ===
content = content.replace(
    "*Last updated: 2026-03-09 (v2 -- added Community Detection, PageRank, Practice Exercises)*",
    "*Last updated: 2026-03-10 (v3 -- added NER Engine, DuckDB, QueryConsole, 2 new exercises, updated interview prep)*"
)

with open(GUIDE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! Updated STUDY_GUIDE.md ({len(content):,} bytes)")
