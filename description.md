# The Superpositioned Press — Implementation Description

**Elbek Rakhmanov** | `er22083`

---

## What Has Been Implemented

### Playable Prototype

A fully playable, single-file Python game (`superpositioned_press.py`) built with **Pygame** and **Pillow**, covering the complete 7-day game cycle described in the proposal.

### Core Game Loop

- **Turn-based structure:** 7 in-game days × 10 turns per day
- **Story feed:** Up to 8 active stories at any time; new stories spawn each turn and expire if ignored
- **Resources:** A journalist pool (5 units/day, restored each morning) that limits how many actions can be taken per day
- **Public Trust score:** Increases on true publications, decreases on fake ones; hitting 0 ends the game

### Quantum Mechanics (the central mechanic)

Every news story holds a quantum state modelled as a two-component vector:

```
|ψ⟩ = α|Truth⟩ + β|Fake⟩     where |α|² + |β|² = 1
```

The angle θ parametrises the state: `α = cos(θ/2)`, `β = sin(θ/2)`, so `|α|² = cos²(θ/2)` is the probability of a Truth outcome on measurement.

Three quantum-inspired actions are implemented:

| Action | Quantum concept | Effect |
|---|---|---|
| **Investigate** | Weak measurement / observer effect | Nudges θ toward 0 (Truth) without collapsing the state; costs 1 journalist |
| **Cross-Reference** | Quantum interference (constructive / destructive) | Compares the phase angles of a story's sources; aligned phases → constructive (large θ shift toward Truth); opposing phases (~π apart) → destructive (θ pushed toward π/2, i.e. 50/50) |
| **Publish** | Wave-function collapse | Draws a random number against `cos²(θ/2)`; story irreversibly becomes Truth or Fake |

This goes beyond simple probability: the *phase alignment* of sources determines whether cross-referencing helps or hurts, making the mechanic structurally different from a dice roll.

### UI

- Animated quantum probability bar with a live wave oscillation overlay (amplitude proportional to uncertainty)
- Source phase diagram (unit-circle vector plot) that previews whether cross-referencing will be constructive or destructive
- Story feed with per-story mini probability bars, deadline countdown, and importance stars
- Persistent newsroom log showing all events colour-coded by outcome
- Main menu with animated title and game summary
- Win / Game-Over end screen with full run statistics

### Win / Lose Conditions

| Condition | Trigger |
|---|---|
| Victory | Survive 7 days with Trust ≥ 60% |
| Defeat (Trust) | Trust reaches 0 from fake publications |
| Defeat (Week ends) | Trust below 60% when the 7-day cycle ends |

---

## How to Run

```bash
python3 superpositioned_press.py
```

**Dependencies:** `pygame`, `Pillow` (`pip install pygame pillow`)

**Controls:** `1` Investigate · `2` Cross-Reference · `3` Publish · `4` Skip Turn · `ESC` Deselect

---

## Use of AI Tools

**Claude Code (Anthropic)** was used as a coding assistant throughout the development of this project.

### Where it was used

1. **Initial code generation** — the full game (`superpositioned_press.py`) was written with Claude Code. I described the game concept from `proposal.md`, and Claude translated it into working Pygame code, including the quantum state model, interference logic, UI layout, and game loop.

2. **Bug fixing** — the game hit a runtime crash on Python 3.14 caused by a circular-import regression in `pygame.font` and `pygame.freetype`. Claude diagnosed the root cause (the `font.py ↔ sysfont.py` circular dependency that Python 3.14 no longer silently tolerates) and rewrote the font system to use **Pillow** (`PIL`) instead, which bypasses the issue entirely.

3. **Proposal formatting** — `proposal.md` was reformatted from plain text to structured Markdown (tables, code blocks, headings) with Claude's help.

### What I contributed

- The original game concept, quantum mechanics mapping, and narrative design (see `proposal.md`)
- Reviewing and testing all generated code to verify the quantum logic was correct and the game was actually playable
- Directing Claude toward specific fixes when the game crashed
