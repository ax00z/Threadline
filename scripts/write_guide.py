"""Write the STUDY_GUIDE.md to Desktop."""

GUIDE = r"""# Threadline -- Complete Project Study Guide

> A deep-dive into every concept, pattern, and design decision in your project.
> Use this to review before interviews, explain your project on your resume, or find what to build next.

---

## Table of Contents

1. What Threadline Actually Is
2. Architecture Overview
3. Phase 1 -- The Streaming Parser
4. Phase 2 -- The Graph Engine (+ Community Detection & PageRank)
5. The REST API (FastAPI)
6. The Frontend (SvelteKit + Sigma.js)
7. Testing Strategy
8. Core CS Concepts You Can Talk About
9. Hands-On Practice Exercises
10. What to Work On Next
11. Interview Talking Points

---

## 1. What Threadline Actually Is

**One-liner**: An investigative analysis platform that turns raw chat exports (WhatsApp, Telegram, SMS) into interactive network graphs and timelines -- built for law enforcement analysts working with seized device data.

**The problem it solves**: When police seize a phone, they get massive .txt chat exports. Analysts currently paste them into Excel and manually highlight names. That is insane for 50k+ messages. Threadline automates the entire pipeline:

```
Raw chat file (.txt/.json/.csv)
  -> Streaming parser (O(1) memory)
    -> NetworkX graph (who talks to who, how often)
      -> Centrality metrics + PageRank + Community Detection
        -> Interactive web dashboard (Sigma.js + Chart.js)
```

**Why this is a strong portfolio project**:
- Real-world domain (forensics/OSINT) -- not another todo app
- Touches parsing, graph theory, NLP, data viz, full-stack
- Performance-conscious (streaming, memory constraints)
- Multi-language architecture (Python + Rust + TypeScript)

---

## 2. Architecture Overview

```
+---------------------------------------------------+
|                   USER BROWSER                     |
|  SvelteKit (port 5173)                            |
|  +----------+ +----------+ +------------------+   |
|  |DropZone  | |Timeline  | | NetworkGraph     |   |
|  |(upload)  | |(Chart.js)| | (Sigma.js +      |   |
|  |          | |          | |  Graphology +     |   |
|  |          | |          | |  ForceAtlas2)     |   |
|  +----------+ +----------+ +------------------+   |
|  +----------+ +----------+ +------------------+   |
|  |StatsBar  | |MsgTable  | | CommunityPanel   |   |
|  +----------+ +----------+ +------------------+   |
+---------------+-----------------------------------+
                | POST /api/upload (multipart)
                | Vite proxy -> :8000
                v
+---------------------------------------------------+
|              PYTHON BACKEND (FastAPI)               |
|                                                     |
|  api.py                                             |
|  +-----------+   +------------------------------+  |
|  | Upload    |-->| parser.py (streaming gen)     |  |
|  +-----------+   +------------------------------+  |
|       |                                             |
|       v                                             |
|  +-----------------------------------------------+ |
|  | _build_graph()                                 | |
|  |  - degree / betweenness / closeness centrality | |
|  |  - PageRank (eigenvector importance)           | |
|  |  - Louvain community detection                 | |
|  +-----------------------------------------------+ |
+---------------------------------------------------+
```

---

## 3. Phase 1 -- The Streaming Parser

**Files**: src/threadline/parser.py, src/threadline/models.py

### 3.1 The Message Dataclass

```python
@dataclass(slots=True)
class Message:
    timestamp: str
    sender: str
    body: str
    line_number: int
    source_format: str = ""
    entities: list = field(default_factory=list)
```

**Key concepts**:
- **@dataclass** -- Auto-generates __init__, __repr__, __eq__
- **slots=True** -- Fixed struct layout, ~40% less memory per instance
- **field(default_factory=list)** -- Avoids mutable default trap (interview favorite)

### 3.2 The Generator Pattern (O(1) Memory)

```python
def _parse_whatsapp(path: str) -> Generator[Message, None, None]:
    for raw in fh:       # ONE line at a time
        yield Message(   # ONE message, not stored
```

- yield pauses execution, returns one item. Caller pulls with for loop.
- Only ONE message in memory at any time. Rest on disk or garbage-collected.
- Proved flat at 384 KB across 50k messages.

### 3.3 Regex Patterns

```python
_BRACKET = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]\s*([^:]+):\s*(.+)$"
)
```

4 capture groups: date, time, sender, body. Multi-line handled by appending to previous.

### 3.4 System Message Filtering
Removes "Alice added Bob", encryption notices. Keeps graph edges clean.

### 3.5 Strategy Pattern
detect_format() dispatches by extension. Same Generator[Message] interface, different parsers.

### 3.6 CSV Flexible Columns
Fuzzy-matches "sender"/"from"/"author". Auto-detects delimiter with csv.Sniffer.

---

## 4. Phase 2 -- The Graph Engine

**File**: src/threadline/api.py -> _build_graph()

### 4.1 What the Graph Represents

```
Nodes = People       |  Edges = Conversations (within 5-min window)
Edge Weight = Number of message exchanges
Type: Undirected weighted graph
```

### 4.2 The Reply Window

```python
_REPLY_WINDOW_SECS = 300  # 5 minutes
```

Sequential messages from different senders within 5 min create/strengthen an edge.

### 4.3 Centrality Metrics

#### Degree Centrality
- How many direct connections?
- Formula: connections / total possible. Range 0-1.
- High = talks to many people (the coordinator)

#### Betweenness Centrality
- How often on shortest path between others?
- High = BRIDGE between groups. Remove them, network fragments.
- **MOST IMPORTANT FOR INVESTIGATIONS** -- finds the broker/middleman

#### Closeness Centrality
- How quickly can you reach everyone?
- Formula: (N-1) / sum(shortest paths). Range 0-1.
- High = information hub, reachable from everywhere

### 4.4 PageRank [BUILT]

```python
pagerank = nx.pagerank(G, weight="weight")
```

- Google's original algorithm applied to communication networks
- Not just HOW MANY connections, but HOW IMPORTANT those connections are
- A person connected to 2 high-PageRank people outranks someone connected to 10 nobodies
- Under the hood: models a "random walker" on the graph. PageRank = probability walker lands on you at steady state (Markov chain)
- Iterative convergence: starts equal, redistributes, repeats until stable

### 4.5 Community Detection -- Louvain [BUILT]

```python
community_sets = nx.community.louvain_communities(G, weight="weight", seed=42)
```

- Automatically partitions graph into subgroups (communities)
- Optimizes "modularity" -- dense connections within communities, sparse between
- **How Louvain works** (2 alternating phases):
  1. Each node = its own community. Try moving each node to neighbor's community. Accept if modularity increases.
  2. Once stable, collapse each community into a super-node. Repeat until no improvement.
- seed=42 makes it deterministic (same input = same result every time)
- **Investigation value**: "There are 3 separate groups" is immediate actionable intel

**What we built on the frontend**:
- Nodes colored by community (same community = same color)
- CommunityPanel shows: member lists, top-3 by PageRank per group, cross-community bridges
- Bridge detection: high betweenness nodes connecting different communities

---

## 5. The REST API (FastAPI)

**FastAPI** = Starlette (async) + Pydantic (validation) + Uvicorn (ASGI).

**Middleware**: GZip (80% compression) + CORS (cross-origin browser requests).

**Upload flow**: receive file -> validate ext -> temp file -> parse -> stats -> graph -> JSON -> cleanup.

**Response now includes**:
- messages[] -- all parsed messages
- stats{} -- counts, date range, senders
- graph.nodes[] -- each with degree, betweenness, closeness, pagerank, community
- graph.edges[] -- source, target, weight
- graph.communities[] -- id, members, size, total_messages

---

## 6. The Frontend (SvelteKit + Sigma.js)

### Why SvelteKit
- No virtual DOM -- compiles to direct DOM updates
- Svelte 5 runes ($state, $derived) -- no useState/useEffect boilerplate
- Smaller bundle -- no runtime shipped

### State Management
- $state() -- reactive state, triggers re-render
- $derived() -- auto-computed, like useMemo without dependency arrays

### Components (updated)
- DropZone -- drag/drop + click file upload
- StatsBar -- message count, participants, date range, avg/day
- SenderStats -- Chart.js horizontal bar chart
- Timeline -- Chart.js daily activity
- MessageTable -- searchable message log
- NetworkGraph -- Sigma.js + Graphology + ForceAtlas2, nodes colored by COMMUNITY
- **CommunityPanel [NEW]** -- community members, PageRank rankings, bridge nodes

### Network Graph
1. Build Graphology graph from API data
2. Circle layout -> ForceAtlas2 physics (200 iterations)
3. Sigma.js WebGL rendering
4. **Nodes colored by community** (not by sender)
5. Hover tooltip: name, community, PageRank, degree, betweenness, closeness
6. Node size = 5 + degree_centrality * 20

---

## 7. Testing Strategy

### 14 Unit Tests
WhatsApp bracket/dash, 24h time, multi-line, system filtering, Telegram JSON, CSV, auto-detection, serialization.

### O(1) Memory Test
Generates 50k messages, samples memory every 5k, asserts peak < 5x first sample.

---

## 8. Core CS Concepts

**Generators**: Lazy eval, O(1) memory, yield vs return, iterator protocol
**Graph Theory**: Weighted graphs, centrality (degree/betweenness/closeness), PageRank, Louvain communities, ForceAtlas2
**Regex**: Finite automata, capture groups, state machines
**REST APIs**: Multipart upload, middleware (CORS, GZip), ASGI vs WSGI
**Frontend**: Component arch, reactivity, compiled vs runtime, WebGL vs SVG
**Patterns**: Strategy, generator/iterator, separation of concerns, property testing
**Performance**: O(1) vs O(n), streaming vs buffering, __slots__, WebGL at scale
**Algorithms**: PageRank (Markov chains, eigenvectors), Louvain (modularity optimization, greedy agglomeration)

---

## 9. Hands-On Practice Exercises

These are things you can do RIGHT NOW to make each concept stick. Open a Python shell, read the code, and try them.

### Exercise 1: Generators (15 min)

Open a Python shell and build your own generator:

```python
# 1a. Write a generator that yields Fibonacci numbers
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

gen = fib()
print([next(gen) for _ in range(10)])

# 1b. Now write a generator that reads a file line-by-line
# and yields only lines containing a keyword.
# Compare memory usage vs reading the whole file into a list.

# 1c. Read src/threadline/parser.py lines 45-90.
# Trace through _parse_whatsapp manually with 3 sample lines.
# What happens when a line does NOT match the regex?
```

**What to explain in an interview**: "Generators use yield to produce items lazily. The function's state is frozen between yields. This gives O(1) memory because only one item exists at a time."

### Exercise 2: Graph Centrality (20 min)

```python
# Open a Python shell in the Threadline directory
import networkx as nx

# 2a. Build a small graph by hand
G = nx.Graph()
G.add_edge("Alice", "Bob", weight=5)
G.add_edge("Bob", "Charlie", weight=2)
G.add_edge("Charlie", "Diana", weight=3)
G.add_edge("Alice", "Diana", weight=1)

# 2b. Compute centrality
print("Degree:", nx.degree_centrality(G))
print("Betweenness:", nx.betweenness_centrality(G))
print("Closeness:", nx.closeness_centrality(G))
print("PageRank:", nx.pagerank(G, weight="weight"))

# 2c. Now add a node "Eve" connected ONLY to Bob.
# Predict: who has highest betweenness now? Check.
# Why? Bob is the only path to Eve from everyone else.

# 2d. Remove the Alice-Diana edge. How does betweenness change?
# Bob and Charlie become the only bridges. Verify.
```

**What to explain**: "Betweenness finds brokers. PageRank finds people connected to important people. Degree just counts connections."

### Exercise 3: Louvain Communities (15 min)

```python
# 3a. Use the graph from Exercise 2, add a second cluster
G.add_edge("Frank", "Grace", weight=4)
G.add_edge("Grace", "Hank", weight=3)
G.add_edge("Frank", "Hank", weight=2)
# Bridge: connect the two clusters
G.add_edge("Charlie", "Frank", weight=1)

comms = nx.community.louvain_communities(G, seed=42)
print("Communities:", comms)
# Expected: roughly {Alice, Bob, Charlie, Diana} and {Frank, Grace, Hank}

# 3b. Increase the Charlie-Frank edge weight to 10. Rerun.
# Does the community structure change? Why?

# 3c. Read src/threadline/api.py lines 61-66.
# Trace how community IDs are assigned to nodes.
```

**What to explain**: "Louvain optimizes modularity -- it tries to maximize within-group edges and minimize between-group edges. The algorithm is greedy and hierarchical."

### Exercise 4: Regex (15 min)

```python
import re

# 4a. Parse this WhatsApp line manually
line = "[3/15/25, 2:30:00 PM] Alice: hey check this out"
pattern = r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]\s*([^:]+):\s*(.+)$"
m = re.match(pattern, line)
print(m.groups())
# ('3/15/25', '2:30:00 PM', 'Alice', 'hey check this out')

# 4b. Try a line that WON'T match (system message):
line2 = "[3/15/25, 2:31 PM] Messages and calls are end-to-end encrypted"
m2 = re.match(pattern, line2)
print(m2)  # None -- no "sender: body" pattern

# 4c. Write a regex that extracts phone numbers from text:
# Match: +1-555-123-4567, (555) 123-4567, 555.123.4567
# This is exactly what the NER phase will do.
```

### Exercise 5: FastAPI (20 min)

```python
# 5a. Start the API: python -m threadline.api
# 5b. Open http://127.0.0.1:8000/docs
#     -- This is auto-generated OpenAPI documentation
#     -- Click "Try it out" on /api/upload, upload a test file
#     -- Examine the JSON response structure

# 5c. Use curl to test:
# curl -X POST http://127.0.0.1:8000/api/upload -F "file=@data/test_communities.txt"
# Pipe through: | python -m json.tool | head -50

# 5d. Read src/threadline/api.py
# Find: Where is the temp file created? Where is it deleted?
# Why is it in a `finally` block? (Hint: exception safety)
```

### Exercise 6: Svelte Reactivity (15 min)

```
# 6a. Open web/src/routes/+page.svelte
# Find every $state() and $derived() call.
# Draw the dependency graph: which derived values depend on which state?

# 6b. Open web/src/lib/components/NetworkGraph.svelte
# Trace the onMount lifecycle:
#   1. What happens first? (Graphology graph creation)
#   2. What layout runs? (circular -> ForceAtlas2)
#   3. What event handlers are registered? (enterNode/leaveNode)

# 6c. Open web/src/lib/components/CommunityPanel.svelte
# Find the $derived(bridgeNodes()) call.
# What threshold is used for bridges? (betweenness > 0.05)
# Why is betweenness the right metric for bridges?
```

### Exercise 7: Read The Code Challenge (30 min)

Open each file and answer these questions WITHOUT running the code:

```
parser.py:
  - What happens if a WhatsApp line has no sender (system message)?
  - How does _parse_telegram handle rich text (bold, links)?
  - Why does _parse_csv use csv.Sniffer?

api.py:
  - What HTTP status code is returned for an unsupported file type?
  - Why is the graph built AFTER collecting all messages, not during streaming?
  - How are community summaries sorted?

NetworkGraph.svelte:
  - What determines node size?
  - What prevents edges from being drawn too thick?
  - Why is renderer?.kill() called in onDestroy?

CommunityPanel.svelte:
  - How are "bridge nodes" identified?
  - Why sort communities by total_messages?
  - What does topByPagerank do differently from just sorting by message count?
```

---

## 10. What to Work On Next

### DONE
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
- [ ] K. Multi-Chat Merge -- 3-4 hours

---

## 11. Interview Talking Points

### "Tell me about a project"

"I built Threadline, a forensic analysis platform for law enforcement. It parses WhatsApp/Telegram/CSV exports into interactive network graphs. The backend streams at 35k msg/s with O(1) memory using Python generators. The graph engine computes degree, betweenness, closeness centrality plus PageRank and Louvain community detection. The frontend uses SvelteKit with Sigma.js WebGL rendering. Nodes are colored by automatically detected communities, and a panel highlights cross-community bridge nodes -- the people connecting separate groups."

### "Hardest challenge?"

"WhatsApp's inconsistent format -- multi-line messages, regional timestamps, system noise. Used a state-machine generator approach. Plus designing the reply-window heuristic for edge construction: I needed to decide what constitutes a 'reply' in a group chat with many participants."

### "How to scale?"

"Parser streams already. Large graphs: background Celery/Redis. Sigma.js handles thousands of nodes via WebGL. For 100k+ nodes: approximate centrality algorithms or graph-tool (C backend, 100x faster than NetworkX)."

### "Explain community detection"

"I use the Louvain algorithm which optimizes modularity -- it maximizes within-community edges and minimizes between-community edges. It's greedy and hierarchical: nodes start alone, get merged into communities, then communities get merged. I also identify bridge nodes using betweenness centrality -- these are people connecting different communities, often the most interesting targets in an investigation."

### "Testing?"

"14 unit tests for every parser format. Plus a property-based O(1) memory test that generates 50k messages and proves memory stays flat at 384KB. The graph engine is verified by generating test data and checking community assignments and centrality rankings match expected patterns."

---

## Quick Reference

```bash
# Python API
cd Threadline && pip install -e ".[dev]" && python -m threadline.api

# Svelte UI
cd Threadline/web && npm install && npm run dev

# Test data
python scripts/gen_test_data.py -n 10000 -o data/test.txt

# Tests
pytest -v

# Quick graph test in Python shell
from threadline.parser import parse_file
from threadline.api import _build_graph
msgs = [m.to_dict() for m in parse_file("data/test_communities.txt")]
g = _build_graph(msgs)
print(f"{len(g['communities'])} communities, {len(g['nodes'])} nodes")
```

---

*Last updated: 2026-03-09 (v2 -- added Community Detection, PageRank, Practice Exercises)*
"""

dst = "C:/Users/roofie/Desktop/STUDY_GUIDE.md"
with open(dst, "w", encoding="utf-8") as f:
    f.write(GUIDE)

import os
print(f"OK: {os.path.getsize(dst):,} bytes written to {dst}")
