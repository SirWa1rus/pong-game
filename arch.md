# Flip Pong: Architecture / Agent Handoff

Read this before changing the project. Also read `spec.md` (features) and `CLAUDE.md`
(rules: ask before any git command, Python only, tests for logic only, do NOT read
`problem.md`, keep this file updated).

## What it is
Pong against a computer opponent, with one twist: when side switching is enabled,
the board randomly flips every 8–15 seconds. Written in Python with **pygame-ce**;
runs on the desktop, and in a web browser via **pygbag** (Python compiled to
WebAssembly).

## Decisions made with the user (interview, 2026-11-13)
| Question | Decision |
|---|---|
| How it's a web app | pygame + pygbag (all game code stays Python) |
| What a "flip" is | Each flip randomly picks **rotate** (board turns 90°, paddles go to top/bottom walls) or **swap** (player and computer trade left/right). Each one toggles, so flipping the same way twice undoes it. |
| Win condition | First to **5** points; then a game-over screen with a "Main Menu" button |
| Flip timing | Random **8–15 s** of play; ball freezes with a 1 s "FLIP INCOMING" warning, then 0.6 s pause after |

Additions not in the spec (small, for usability): Esc returns to the menu during a
game; the player paddle is white and the computer paddle is red; there's an on-screen
hint while the board is rotated.

## Layout
```
pong-game/
  game/                 <- the folder pygbag packages (keep it small!)
    main.py             screens + async game loop (pygame)
    pong/logic.py       pure rules, NO pygame import (unit tested)
    pong/ui.py          Button, Slider, draw_block_title (pygame widgets)
  tests/test_logic.py   pytest tests for pong/logic.py only
  pytest.ini            pythonpath = game, so tests can `import pong`
  requirements.txt      pygame-ce, pygbag, pytest
  .venv/                virtual environment (git-ignored)
```
Why `game/` is separate: pygbag bundles *every* file in the folder it builds. Building
the project root packed `.venv` (12 MB). Building `game/` gives about 7 KB.

## Key design: the logical frame
`logic.Game` always simulates a FIELD×FIELD (600×600) board with the **player on the
left wall, computer on the right**, paddles moving along y. Flips never touch the
physics. They only set `game.rotated` / `game.swapped`, and drawing maps every
logical rectangle through `logic.rect_to_screen`:
- swapped → `x = FIELD - x` (mirror)
- rotated → `(x, y) = (y, x)` (left wall becomes top wall)

Input goes through `logic.player_direction(up, down, left, right, rotated)`. When
rotated, only left/right (or A/D) move the paddle; logical "up" = screen left.

## Game.update(dt, direction) order
1. If there's a winner, do nothing.
2. If a flip warning is showing, count it down → `apply_flip(kind)` → short pause.
3. Move the player and the computer paddles.
4. If `pause > 0` (serve delay / post-flip), count down and stop.
5. Count down `flip_timer` (if enabled) → start a warning with a random kind.
6. Move the ball: wall bounce, paddle bounce (angle from hit offset, +6% speed,
   capped at 720), scoring. Each point re-serves toward the player who lost it.

Computer AI: chases `ball.y + ai_error` only while the ball is coming at it,
otherwise it returns to center. Difficulty (`DIFFICULTIES`) sets its speed fraction
and aim error.

## Screens (`App.state` in main.py)
`menu` → `setup` (difficulty slider left, side-switch slider right, Go Back bottom
left, Start Game bottom right) → `game` → `gameover` → `menu`. `controls` has a Go
Back button. Exit stops the loop (in a browser the canvas just stops).
Buttons: `RED` = HSV(0, 0.60, 0.85); hover = same hue/value, saturation 1.0.

## How to run (Git Bash on Windows, from `pong-game/`)
```bash
python -m venv .venv                 # first time only
source .venv/Scripts/activate
pip install -r requirements.txt      # first time only
python -m pytest                     # tests
python game/main.py                  # desktop window
python -m pygbag game                # browser: open http://localhost:8000
```

## Ideas / not done yet
- Sound effects, two-player mode, pause key.
- `ui.Slider` snapping isn't unit tested (it's UI, and tests are logic-only by rule).
