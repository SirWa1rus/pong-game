# Chat history

## 2026-11-13: Building the game from spec.md

**User:** build the program in spec.md

**Agent:** Read spec.md / arch.md / history.md (not problem.md). The spec left some
decisions open, so the agent interviewed the user:
- *How should a Python game be a web app?* → **User:** Pygame + pygbag
- *What happens when the sides flip?* → **User:** Both, at random (90° rotation or
  left/right swap)
- *How does a match end?* → **User:** First to 5
- *How often do flips happen?* → **User:** Random 8–15 seconds

**Agent:** Started creating a virtual environment and installing pygame-ce, pygbag,
and pytest.

**User:** (cancelled the command by accident) hit esc on accident my mistake

**Agent:** Re-ran the install. Built `pong/logic.py` (pure rules), `pong/ui.py`
(buttons, sliders, block title), `main.py` (screens + async loop), and 23 logic
tests (all pass). Rendered every screen headlessly to check the layout. The first
pygbag build packed the `.venv` folder (12 MB), so the agent moved the game into
`game/` (bundle now about 7 KB) and added `pytest.ini`, `.gitignore`, and
`requirements.txt`. Wrote `arch.md`.

**Agent:** Summarized the build, gave Git Bash run steps, asked a check question
(which keys move the paddle after a 90° flip), and asked permission to commit.

**User:** ill take a look at everythign before I commit

**Agent:** Held off on committing. Suggested a review order (arch.md → logic.py →
tests → main.py/ui.py), a test-breaking experiment, and `git status` / `git diff`
to inspect changes.

## 2026-11-16

**User:** what uses requirements.txt?

**Agent:** Explained that only pip reads it (`pip install -r requirements.txt`), and
that it's how the git-ignored `.venv` gets rebuilt after cloning. Noted the file
lists no version numbers (`pygame-ce==2.5.8` would pin one; `pip freeze` shows the
installed versions). Asked a check question and offered to record the question.

**User:** dont forget to update history.md

**Agent:** Added the messages since the build to history.md.
