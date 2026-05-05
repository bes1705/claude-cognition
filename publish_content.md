# Publication Content — claude-cognition

---

## LINKEDIN POST

Claude est brillant. Mais il oublie tout entre chaque session.

Hier tu lui as expliqué ton stack, tes décisions d'architecture, tes erreurs passées.
Aujourd'hui, tu recommences. Chaque fois. Sans exception.

J'ai construit claude-cognition pour résoudre ça.

Un graphe cognitif à 3 couches qui survit à chaque session :

Épisodique — tes décisions avec leur raisonnement
"J'ai choisi Redis plutôt que Postgres parce que la latence devait être sous 10ms"

Sémantique — les faits sur toi et ton projet
"Stack : FastAPI + React. Deploy : VPS Hetzner. Port : 22."

Procédural — les patterns qui marchent
"Toujours vérifier le funding rate avant d'ouvrir une position"

Et une couche temporelle qui n'existe nulle part ailleurs : quand tu t'apprêtes à répéter une erreur passée, Claude te le dit avant que tu la fasses.

"Tu es sur le point de modifier la config. La dernière fois que tu as fait ça sous pression, ça a causé 6h d'indisponibilité."

Installation en 1 commande :
git clone https://github.com/bes1705/claude-cognition
python install.py

Zéro dépendance externe. 100% offline. S'intègre via les hooks natifs de Claude Code.

GitHub : https://github.com/bes1705/claude-cognition

#ClaudeCode #AI #DeveloperTools #OpenSource #LLM

---

## REDDIT POST — r/ClaudeAI

**Title:** I built a persistent 3-layer cognitive memory for Claude Code — zero deps, works offline

**Body:**

Every Claude Code session starts from zero. You re-explain your stack, your past decisions, your constraints. Every. Single. Time.

I built **claude-cognition** to fix that.

**How it works:**

Three memory layers that survive sessions:

1. **Episodic** — decisions with their *why* ("chose Redis over Postgres — latency < 10ms required")
2. **Semantic** — facts about you and your project ("stack: FastAPI + React · deploy: Hetzner VPS")
3. **Procedural** — patterns that work ("always run tests before pushing")

Plus a **temporal guard layer** that's new: when you're about to repeat a known mistake, Claude tells you before you do it.

```
$ cognition detect "I'm about to modify the production config"

⚠️  COGNITION ALERT — 1 pattern detected:
  Pattern : never modify bot config without running tests
  Outcome : caused 6h outage in April
  Hits    : 3 times
```

**Install:**
```bash
git clone https://github.com/bes1705/claude-cognition
cd claude-cognition
python install.py  # patches settings.json automatically
```

The installer adds two hooks:
- `SessionStart` → injects your top memories into every new session
- `Stop` → auto-snapshots project state (git log, recent changes)

**Zero external dependencies.** Pure Python stdlib. Fully offline. All data in `~/.cognition/`.

GitHub: https://github.com/bes1705/claude-cognition

Would love feedback — especially on the temporal detection approach.

---

## ZENODO METADATA

**Title:** Claude Cognition: Persistent 3-Layer Cognitive Memory Graph for Claude Code

**Authors:** Stadelmann, Sébastien

**Description:**
Claude Cognition is an open-source Python package implementing a persistent 3-layer cognitive memory graph for Claude Code (Anthropic). The system addresses the universal problem of session amnesia in LLM interactions.

Architecture: (1) Episodic layer — timestamped decisions with reasoning; (2) Semantic layer — persistent facts as key-value pairs with confidence scores; (3) Procedural layer — validated patterns and workflows. Additionally, a Temporal Guard Layer detects negative pattern repetition before errors occur.

Integration via Claude Code native hooks: SessionStart injects ranked context, Stop captures project snapshots automatically.

**Keywords:** claude-code, persistent-memory, cognitive-graph, llm-memory, session-continuity, temporal-pattern-detection, episodic-memory, procedural-memory, prior-art, open-source

**License:** MIT

**Upload URL:** https://zenodo.org/uploads/new
