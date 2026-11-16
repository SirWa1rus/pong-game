"""Tests for pong/logic.py (game rules only; no pygame needed)."""

import random

import pytest

from pong import logic
from pong.logic import FIELD, Game


def make_game(**kwargs):
    """A game with a fixed random seed and the serve pause already over."""
    game = Game(rng=random.Random(0), **kwargs)
    game.pause = 0
    return game


# ---------- screen mapping for flips ----------

def test_to_screen_normal_is_unchanged():
    assert logic.to_screen(10, 50, rotated=False, swapped=False) == (10, 50)


def test_to_screen_swap_mirrors_left_right():
    assert logic.to_screen(10, 50, rotated=False, swapped=True) == (FIELD - 10, 50)


def test_to_screen_rotate_moves_left_wall_to_top():
    # A point near the left wall ends up near the top wall.
    assert logic.to_screen(10, 50, rotated=True, swapped=False) == (50, 10)


def test_rect_to_screen_rotate_swaps_width_and_height():
    _, _, w, h = logic.rect_to_screen(300, 300, 12, 90, rotated=True, swapped=False)
    assert (w, h) == (90, 12)


# ---------- controls ----------

def test_up_down_keys_move_paddle_normally():
    assert logic.player_direction(up=True, down=False, left=False, right=False, rotated=False) == -1
    assert logic.player_direction(up=False, down=True, left=False, right=False, rotated=False) == 1


def test_left_right_ignored_when_not_rotated():
    assert logic.player_direction(up=False, down=False, left=True, right=True, rotated=False) == 0


def test_left_right_keys_used_when_rotated():
    assert logic.player_direction(up=False, down=False, left=True, right=False, rotated=True) == -1
    assert logic.player_direction(up=True, down=False, left=False, right=True, rotated=True) == 1


# ---------- paddles ----------

def test_paddle_stays_inside_field():
    game = make_game()
    for _ in range(200):
        game.update(1 / 60, -1)
    assert game.player.y == logic.PADDLE_LEN / 2


# ---------- ball physics ----------

def test_ball_bounces_off_top_wall():
    game = make_game()
    game.ball.x, game.ball.y = FIELD / 2, 5
    game.ball.vx, game.ball.vy = 0, -300
    game.update(1 / 60, 0)
    assert game.ball.vy > 0


def test_ball_bounces_off_player_paddle_and_speeds_up():
    game = make_game()
    game.player.y = FIELD / 2
    game.ball.x, game.ball.y = game.player.x + 15, FIELD / 2
    game.ball.vx, game.ball.vy = -400, 0
    game.update(1 / 60, 0)
    assert game.ball.vx > 0
    assert game.ball.speed == pytest.approx(400 * logic.SPEEDUP)


def test_hitting_paddle_edge_gives_angle():
    game = make_game()
    game.ball.x, game.ball.y = game.player.x + 15, game.player.y + 40
    game.ball.vx, game.ball.vy = -400, 0
    game.update(1 / 60, 0)
    assert game.ball.vy > 0     # hit below center -> goes downward


def test_ball_speed_is_capped():
    game = make_game()
    game.ball.x, game.ball.y = game.player.x + 15, game.player.y
    game.ball.vx, game.ball.vy = -logic.BALL_MAX_SPEED, 0
    game.update(1 / 120, 0)
    assert game.ball.speed == pytest.approx(logic.BALL_MAX_SPEED)


# ---------- scoring ----------

def test_ball_past_left_wall_scores_for_computer():
    game = make_game()
    game.player.y = logic.PADDLE_LEN / 2          # paddle out of the way
    game.ball.x, game.ball.y = 2, FIELD - 50
    game.ball.vx, game.ball.vy = -300, 0
    game.update(1 / 60, 0)
    assert game.computer_score == 1
    assert (game.ball.x, game.ball.y) == (FIELD / 2, FIELD / 2)   # re-served
    assert game.ball.vx < 0                                        # toward the loser


def test_first_to_five_wins():
    game = make_game()
    game.player_score = logic.WIN_SCORE - 1
    game._point("player")
    assert game.winner == "player"


def test_no_updates_after_win():
    game = make_game()
    game.winner = "computer"
    before = (game.ball.x, game.ball.y)
    game.update(1, 1)
    assert (game.ball.x, game.ball.y) == before


# ---------- computer player ----------

def test_computer_moves_toward_incoming_ball():
    game = make_game()
    game.ai_error = 0
    game.ball.y, game.ball.vx = 100, 300
    start = game.computer.y
    game._move_computer(0.1)
    assert game.computer.y < start


@pytest.mark.parametrize("slow, fast", [("Easy", "Medium"), ("Medium", "Hard")])
def test_harder_computer_moves_faster(slow, fast):
    moved = {}
    for level in (slow, fast):
        game = make_game(difficulty=level)
        game.ai_error = 0
        game.ball.y, game.ball.vx = 0, 300
        start = game.computer.y
        game._move_computer(0.1)
        moved[level] = start - game.computer.y
    assert moved[fast] > moved[slow]


# ---------- side flips ----------

def test_no_flips_when_disabled():
    game = make_game(flips_enabled=False)
    for _ in range(60 * 30):           # 30 seconds
        game.update(1 / 60, 0)
        assert game.warning <= 0
    assert not game.rotated and not game.swapped


def test_flip_timer_is_between_8_and_15_seconds():
    game = make_game(flips_enabled=True)
    assert logic.FLIP_MIN <= game.flip_timer <= logic.FLIP_MAX


def test_flip_shows_warning_then_flips():
    game = make_game(flips_enabled=True)
    game.flip_timer = 0.01
    game.update(1 / 60, 0)
    assert game.warning > 0 and game.pending_flip in logic.FLIP_KINDS

    ball_before = (game.ball.x, game.ball.y)
    game.update(0.5, 0)
    assert (game.ball.x, game.ball.y) == ball_before   # frozen during warning

    kind = game.pending_flip
    game.update(0.6, 0)
    assert game.rotated if kind == "rotate" else game.swapped
    assert game.pause > 0                               # brief freeze after flip


def test_flipping_twice_returns_to_normal():
    game = make_game()
    game.apply_flip("rotate")
    game.apply_flip("rotate")
    game.apply_flip("swap")
    game.apply_flip("swap")
    assert not game.rotated and not game.swapped


def test_both_flip_kinds_happen():
    game = make_game(flips_enabled=True)
    seen = set()
    for _ in range(40):
        game.flip_timer = 0.001
        game.pause = 0
        game.update(1 / 60, 0)
        seen.add(game.pending_flip)
        game.update(logic.FLIP_WARNING + 0.01, 0)
    assert seen == {"rotate", "swap"}
