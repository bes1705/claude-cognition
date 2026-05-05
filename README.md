# cognition

**Persistent 3-layer cognitive memory for Claude Code.**

Claude is brilliant. But every session, it forgets everything — your stack, your decisions, your mistakes, your *why*.

`cognition` fixes that. It gives Claude Code a living memory that survives sessions: decisions with their reasoning, patterns that worked, and guards that prevent repeating past mistakes.

---

## The problem

Every time you open Claude Code, you re-explain:
- Who you are and what you're building
- Why you chose this architecture
- What broke last time and how you fixed it
- Your team conventions and constraints

That's 10–15 minutes of context re-loading. Every session. Compounding waste.

---

## The solution

`cognition` adds a **3-layer cognitive graph** to Claude Code:

| Layer | What it stores | Example |
|---|---|---|
| **Episodic** | Events, decisions, outcomes | "Chose Redis over Postgres for session cache — latency requirement" |
| **Semantic** | Facts about you and your project | "Stack: FastAPI + React + Postgres · Deploy: VPS Hetzner" |
| **Procedural** | Patterns and workflows that work | "Always run tests before pushing — learned from March incident" |

Plus a **temporal guard layer**: when you're about to repeat a past mistake, `cognition` tells you — before you do it.

> *"You're about to modify the trading bot config. Last time you did this under pressure, it caused a 6-hour outage."*

---

## Install

```bash
git clone https://github.com/bes1705/claude-cognition
cd claude-cognition
python install.py
```

That's it. The installer:
1. Installs the `cognition` CLI
2. Adds a `SessionStart` hook → injects your memory into every new Claude session
3. Adds a `Stop` hook → auto-captures project context when you close a session

---

## Usage

### Save a memory

```bash
# Save a decision with its reasoning
cognition save --type decision "chose Redis over Postgres for sessions — latency < 10ms required"

# Save something to always avoid
cognition save --type avoid "never modify bot config without running tests first — broke prod in April"

# Save a pattern that works
cognition save --type pattern "always check funding rate before opening a futures position"

# Save a fact about your project
cognition save --type fact "deploy: ssh root@178.x.x.x · port 22 · service: jarvis-trade"

# Save a learning
cognition save --type learning "Binance returns 418 when rate-limited, not 429"
```

### Recall memories

```bash
cognition recall "trading bot"
cognition recall "deployment"
cognition recall "react performance"
```

### Detect negative patterns before acting

```bash
cognition detect "I'm about to push directly to main without tests"
# ⚠️  COGNITION ALERT — 1 pattern(s) detected:
#   Pattern : never push without tests
#   Outcome : broke prod in April
#   Hits    : 3 time(s)
```

### Check status

```bash
cognition status
# ── Cognition Status ─────────────────
#   Sessions     : 47
#   Episodic     : 312 memories
#   Semantic     : 28 facts
#   Procedural   : 64 patterns
#   Guards       : 12 negative patterns
#   Storage      : ~/.cognition/
```

### Search everything

```bash
cognition recall "auth bug"
cognition graph  # dump full graph as JSON
```

---

## How it integrates with Claude Code

`cognition` uses Claude Code's native hook system.

**SessionStart** → `cognition inject` runs and outputs your relevant memories directly into Claude's context. Zero re-briefing.

**Stop** → `cognition auto-capture` snapshots your project state (git log, recent changes) automatically.

Example hook output Claude sees at session start:

```markdown
# Cognition Context — my-project · 2026-05-05

## Recent memory
- [DECISION] chose Redis over Postgres for sessions — latency < 10ms required
- [LEARNING] Binance returns 418 when rate-limited, not 429
- [AUTO] Session end snapshot — 3 commits: fix auth · add Redis · deploy to VPS

## Known facts
- deploy: ssh root@178.x.x.x · port 22 · service: jarvis-trade
- stack: FastAPI + React + Postgres

## Active patterns
- always check funding rate before opening a futures position

## Guards — avoid repeating
- AVOID: never modify bot config without running tests first
```

---

## Manual hook setup (optional)

If you prefer manual setup, add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{ "command": "python -m cognition inject" }],
    "Stop": [{ "command": "python -m cognition auto-capture" }]
  }
}
```

---

## Architecture

```
~/.cognition/
├── graph.json          # 3-layer cognitive graph (episodic/semantic/procedural)
├── memories/           # Daily memory files by project
│   └── 2026-05-05_myproject_decision.md
└── cognition.log

cognition/
├── graph.py            # Core graph: store, recall, detect
├── capture.py          # Save memories (manual + auto)
├── inject.py           # Generate context for session injection
├── detect.py           # Temporal pattern detection
└── cli.py              # CLI entry point
```

**No external dependencies.** Pure Python stdlib. Works on Mac, Linux, Windows.

---

## Why this is different from CLAUDE.md

| CLAUDE.md | cognition |
|---|---|
| Manual — you write it | Automatic — Claude writes it |
| Static file | Living graph that grows every session |
| No temporal reasoning | Detects when you're repeating a past mistake |
| One global context | Project-aware, keyword-scored injection |
| No negative patterns | Guards against known failure modes |

---

## Companion project

Built on the same principles as [claude-memory](https://github.com/bes1705/claude-memory) — typed persistent memory with TTL for Claude Code.

`cognition` goes further: it doesn't just store memories, it **reasons** about them temporally.

---

## License

MIT — [bes1705](https://github.com/bes1705)
