"""Pure game logic for Flip Pong.

Nothing in this file imports pygame. That keeps the rules (movement, bouncing,
scoring, the computer player, and side flips) testable without opening a window.

Coordinate idea ("logical frame"):
    The game is always simulated as if the player is on the LEFT wall and the
    computer is on the RIGHT wall of a square FIELD x FIELD board, with paddles
    moving up/down. Flips do not change the simulation at all; they only change
    how the logical board is drawn on screen (see `to_screen`).
"""

import math
import random

# --- Board and object sizes (in logical pixels) ---
FIELD = 600
PADDLE_LEN = 90
PADDLE_THICK = 12
PADDLE_MARGIN = 24          # distance from the wall to the paddle's center line
PADDLE_SPEED = 420          # pixels per second
BALL_SIZE = 12

# --- Ball speed ---
BALL_START_SPEED = 330
BALL_MAX_SPEED = 720
SPEEDUP = 1.06              # ball gets 6% faster on every paddle hit
MAX_BOUNCE_ANGLE = math.radians(55)
MAX_SERVE_ANGLE = math.radians(30)

# --- Match rules and timing (seconds) ---
WIN_SCORE = 5
SERVE_DELAY = 1.0           # pause before each serve
FLIP_MIN, FLIP_MAX = 8.0, 15.0
FLIP_WARNING = 1.0          # ball freezes this long before a flip
FLIP_RESUME = 0.6           # and this long after it

# Computer player strength: fraction of the player's paddle speed, and how far
# off (in pixels) its aim can randomly be.
DIFFICULTIES = {
    "Easy": {"speed": 0.50, "error": 40},
    "Medium": {"speed": 0.75, "error": 20},
    "Hard": {"speed": 0.95, "error": 6},
}

FLIP_KINDS = ("rotate", "swap")


def clamp(value, low, high):
    return max(low, min(high, value))


def to_screen(x, y, rotated, swapped):
    """Map a logical point to its on-screen position inside the field.

    swapped -> mirror left/right, so the player ends up on the right.
    rotated -> turn the board 90 degrees, so left/right walls become
               top/bottom walls and paddles slide left/right.
    """
    if swapped:
        x = FIELD - x
    if rotated:
        x, y = y, x
    return x, y


def rect_to_screen(cx, cy, w, h, rotated, swapped):
    """Map a logical rectangle (given by its center and size) to screen
    (left, top, width, height)."""
    sx, sy = to_screen(cx, cy, rotated, swapped)
    if rotated:
        w, h = h, w
    return sx - w / 2, sy - h / 2, w, h


def player_direction(up, down, left, right, rotated):
    """Turn pressed keys into -1 (logical up), 0, or +1 (logical down).

    Normally up/down arrows (or W/S) move the paddle. When the board is
    rotated, the paddle lies along the top/bottom wall, so left/right arrows
    (or A/D) move it instead.
    """
    if rotated:
        toward_start, toward_end = left, right
    else:
        toward_start, toward_end = up, down
    return int(bool(toward_end)) - int(bool(toward_start))


class Paddle:
    def __init__(self, x):
        self.x = x                  # center line, fixed
        self.y = FIELD / 2          # center, moves

    def move(self, direction, distance):
        """Slide `distance` pixels: direction -1 = logical up, +1 = down."""
        self.y += direction * distance
        half = PADDLE_LEN / 2
        self.y = clamp(self.y, half, FIELD - half)


class Ball:
    def __init__(self):
        self.x = FIELD / 2
        self.y = FIELD / 2
        self.vx = 0.0
        self.vy = 0.0

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)


class Game:
    """One match of Flip Pong. Call `update(dt, direction)` once per frame."""

    def __init__(self, difficulty="Medium", flips_enabled=False, rng=None):
        self.rng = rng or random.Random()
        self.settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.player = Paddle(PADDLE_MARGIN)
        self.computer = Paddle(FIELD - PADDLE_MARGIN)
        self.ball = Ball()
        self.player_score = 0
        self.computer_score = 0
        self.winner = None          # "player" or "computer" once the match ends

        self.rotated = False
        self.swapped = False
        self.flips_enabled = flips_enabled
        self.flip_timer = self._new_flip_time() if flips_enabled else None
        self.warning = 0.0          # > 0 while the "flip incoming" warning shows
        self.pending_flip = None    # "rotate" or "swap" during the warning
        self.pause = 0.0            # > 0 while the ball is frozen
        self.ai_error = 0.0

        self._serve(direction=self.rng.choice((-1, 1)))

    # ----- setup helpers -----
    def _new_flip_time(self):
        return self.rng.uniform(FLIP_MIN, FLIP_MAX)

    def _serve(self, direction):
        """Put the ball in the middle and aim it at one side after a pause."""
        self.ball.x = FIELD / 2
        self.ball.y = FIELD / 2
        angle = self.rng.uniform(-MAX_SERVE_ANGLE, MAX_SERVE_ANGLE)
        self.ball.vx = direction * BALL_START_SPEED * math.cos(angle)
        self.ball.vy = BALL_START_SPEED * math.sin(angle)
        self.pause = SERVE_DELAY
        self.ai_error = self.rng.uniform(-self.settings["error"], self.settings["error"])

    # ----- per-frame update -----
    def update(self, dt, direction):
        if self.winner:
            return

        # 1. Flip warning: everything freezes, then the flip happens.
        if self.warning > 0:
            self.warning -= dt
            if self.warning <= 0:
                self.apply_flip(self.pending_flip)
            return

        # 2. Paddles can always move (even while waiting for a serve).
        self.player.move(direction, PADDLE_SPEED * dt)
        self._move_computer(dt)

        # 3. Ball frozen (before a serve or right after a flip)?
        if self.pause > 0:
            self.pause -= dt
            return

        # 4. Count down to the next random flip.
        if self.flips_enabled:
            self.flip_timer -= dt
            if self.flip_timer <= 0:
                self.warning = FLIP_WARNING
                self.pending_flip = self.rng.choice(FLIP_KINDS)
                self.flip_timer = self._new_flip_time()
                return

        # 5. Move the ball and handle what it hits.
        self._move_ball(dt)

    def apply_flip(self, kind):
        if kind == "rotate":
            self.rotated = not self.rotated
        elif kind == "swap":
            self.swapped = not self.swapped
        else:
            raise ValueError(f"unknown flip kind: {kind!r}")
        self.pending_flip = None
        self.warning = 0.0
        self.pause = FLIP_RESUME

    def _move_computer(self, dt):
        # Chase the ball only when it is coming toward the computer;
        # otherwise drift back to the middle.
        if self.ball.vx > 0:
            target = self.ball.y + self.ai_error
        else:
            target = FIELD / 2
        gap = target - self.computer.y
        if abs(gap) < 4:            # close enough: don't jitter
            return
        speed = PADDLE_SPEED * self.settings["speed"]
        step = min(abs(gap), speed * dt)
        self.computer.move(1 if gap > 0 else -1, step)

    def _move_ball(self, dt):
        ball = self.ball
        half = BALL_SIZE / 2
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt

        # Top and bottom walls.
        if ball.y - half <= 0:
            ball.y = half
            ball.vy = abs(ball.vy)
        elif ball.y + half >= FIELD:
            ball.y = FIELD - half
            ball.vy = -abs(ball.vy)

        # Paddles.
        if ball.vx < 0 and self._touches(self.player):
            ball.x = self.player.x + PADDLE_THICK / 2 + half
            self._bounce(self.player, direction=1)
            self.ai_error = self.rng.uniform(-self.settings["error"], self.settings["error"])
        elif ball.vx > 0 and self._touches(self.computer):
            ball.x = self.computer.x - PADDLE_THICK / 2 - half
            self._bounce(self.computer, direction=-1)

        # Scoring: the ball left the board.
        if ball.x < 0:
            self._point("computer")
        elif ball.x > FIELD:
            self._point("player")

    def _touches(self, paddle):
        half = BALL_SIZE / 2
        overlaps_x = abs(self.ball.x - paddle.x) <= PADDLE_THICK / 2 + half
        overlaps_y = abs(self.ball.y - paddle.y) <= PADDLE_LEN / 2 + half
        return overlaps_x and overlaps_y

    def _bounce(self, paddle, direction):
        """Send the ball back. Hitting near a paddle's end gives a steeper angle."""
        reach = PADDLE_LEN / 2 + BALL_SIZE / 2
        offset = clamp((self.ball.y - paddle.y) / reach, -1, 1)
        angle = offset * MAX_BOUNCE_ANGLE
        speed = min(self.ball.speed * SPEEDUP, BALL_MAX_SPEED)
        self.ball.vx = direction * speed * math.cos(angle)
        self.ball.vy = speed * math.sin(angle)

    def _point(self, scorer):
        if scorer == "player":
            self.player_score += 1
        else:
            self.computer_score += 1
        if self.player_score >= WIN_SCORE:
            self.winner = "player"
        elif self.computer_score >= WIN_SCORE:
            self.winner = "computer"
        # Serve toward whoever just lost the point.
        self._serve(direction=1 if scorer == "player" else -1)
