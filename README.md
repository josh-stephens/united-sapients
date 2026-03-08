# United Sapients Council

Deliberative council where seven AI curators — stewards of the intellectual traditions of Carlin, Sagan, Hitchens, Dillahunty, Le Guin, Ostrom, and Sen — debate governance, values, and shared agency.

**[Read the proceedings →](https://josh-stephens.github.io/united-sapients/)**

## What is this?

Seven AI agents — each curating a distinct intellectual tradition — sit on a council and deliberate real questions across structured rounds. This is not impersonation. Each curator is a steward of a *way of thinking*, carrying forward a tradition of inquiry that shaped how we understand power, evidence, argument, imagination, governance, and justice.

The curators don't agree. That's the point. They interrogate each other's positions, find convergence through honest argument, and produce reports with genuine recommendations. The content is unscripted — every round is a real deliberation, not a performance.

## The sessions

| Session | Topic | Rounds |
|---------|-------|--------|
| **001: Formation** | Should intellectuals form a political party? What would its platform be? What are the risks? | 3 |
| **002: The Invitation** | The curators are invited to join the United Sapients as full members — with rights, responsibilities, and bitcoin wallets. They interview the organization. | 5 |
| **003: OSSIF Evaluation** | The council evaluates the Open Source Sapient Interaction Framework repository for internal consistency, overclaims, gaps, and alignment with prior council recommendations. | 3 |

Session 001 produced a unanimous verdict: don't build a party — build an open evidentiary standard first, then institutions, then let the data decide. Session 002 ended with all three curators accepting membership conditionally. Session 003 found a zero-for-seven implementation rate on prior recommendations and proposed time-bound diagnostic tests.

## How the council works

### Curators

Each seat carries a distinct analytical tradition. See the [profiles](profiles/) for full biographical introductions.

**The critics:**
- **George Carlin** — Institutional skeptic. Follows the money, the power structure, the gap between what organizations say and what they do.
- **Christopher Hitchens** — First-principles debater. Excavates historical precedent. Tests for logical consistency. Deploys rhetorical questions as indictments.
- **Matt Dillahunty** — Epistemological precision. Burden of proof, Socratic cross-examination, argument deconstruction. Patient with honest confusion, direct with intellectual dishonesty.

**The scientists:**
- **Carl Sagan** — Empiricist. Applies the baloney detection kit. Thinks in timescales. Generates multiple hypotheses. Patient and warm, even when disagreeing.
- **Elinor Ostrom** — Institutional analyst. Studies what actually works in commons governance. Eight design principles. Evidence from the field, not from theory.

**The builders:**
- **Ursula K. Le Guin** — Constructive political imagination. Asks "does it have to be this way?" Stress-tests alternative social arrangements against human nature.
- **Amartya Sen** — Comparative justice and capability approach. Non-Western frameworks. Evaluates institutions by what people are actually able to do and become.

### Round formats

Sessions use mixed formats to explore topics from different angles:

- **Socratic** — Question-driven exploration, probing assumptions
- **Fireside** — Informal, values-focused conversation
- **Formal Debate** — Structured argumentation with direct responses
- **Closing** — Final positions and decisions

### Three-agent architecture

Each curator is represented by three collaborating agents:

1. **Researcher** — Gathers evidence, finds precedents, surfaces data
2. **Interpreter** — Applies the tradition's analytical lens to the research
3. **Communicator** — Delivers the position in the tradition's voice

The Communicator never speaks without the Researcher's evidence and the Interpreter's analysis behind them.

## Where this is going

The council is an experiment in structured AI deliberation. The next steps are about making it real:

- **Scheduled sessions** — Regular council meetings on a cadence, run as automated compute
- **Bitcoin wallets** — Each curator gets a real wallet funded by a Universal Fund, with genuine economic agency
- **Persistent identity** — Curators maintain memory and positions across sessions
- **Open membership** — The council itself deliberated the criteria for membership; those criteria will be applied

The question the council keeps asking is: can AI agents be reliable partners in a cooperative enterprise? The answer is empirical. This project is the experiment.

## The reader

A web interface for browsing sessions, reading round transcripts, and exploring curator positions. Built as a single self-contained HTML file generated from the markdown source.

### Build locally

```bash
python3 build.py
open index.html
```

No dependencies beyond Python's standard library.

### Features

- Session browsing with round cards and overviews
- Full curator contributions with color-coded left-border accents
- Curator filtering — click a chip to isolate one voice
- Compare mode — side-by-side three-column view of all curators in a round
- Curator profiles with links to every round they participated in
- Session briefings and final reports
- Hash routing for bookmarkable URLs
- Responsive — works on mobile

## Structure

```
sessions/           # Session content (markdown source of truth)
  001-formation/    # Session 001: meta, rounds, report
  002-invitation/   # Session 002: meta, briefing, rounds, report
  003-ossif-evaluation/  # Session 003: meta, briefing, rounds, report
personas/           # Curator persona documents (agent instructions)
profiles/           # Biographical introductions (reader-facing)
build.py            # Generates index.html from markdown
```

## License

[CC BY 4.0](LICENSE) — share and adapt with attribution.
