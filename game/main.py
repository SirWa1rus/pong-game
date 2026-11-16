"""Flip Pong: Pong where the sides randomly flip.

Run from the pong-game folder (with the .venv activated):
Desktop:  python game/main.py
Browser:  python -m pygbag game     (then open http://localhost:8000)

The loop is `async` because pygbag (the browser runner) needs the game to hand
control back to the browser every frame via `await asyncio.sleep(0)`.
"""

import asyncio

import pygame

from pong import logic
from pong.ui import BLACK, GREY, RED_HOVER, WHITE, Button, Slider, draw_block_title

WIDTH, HEIGHT = 640, 720
FIELD_LEFT, FIELD_TOP = (WIDTH - logic.FIELD) // 2, 100   # where the board sits
FPS = 60


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flip Pong")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 72)
        self.running = True
        self.state = "menu"
        self.game = None

        cx = WIDTH // 2
        # Main menu
        self.start_btn = Button("Start", (cx, 380))
        self.controls_btn = Button("Controls", (cx, 460))
        self.exit_btn = Button("Exit", (cx, 540))
        # Shared corner buttons
        self.back_btn = Button("Go Back", (130, HEIGHT - 60), size=(200, 56))
        self.play_btn = Button("Start Game", (WIDTH - 130, HEIGHT - 60), size=(200, 56))
        self.menu_btn = Button("Main Menu", (cx, 480))
        # Setup sliders: difficulty on the left, side switching on the right
        self.difficulty = Slider("Computer", list(logic.DIFFICULTIES), (WIDTH // 4, 340), width=200, index=1)
        self.flips = Slider("Side Switching", ["Disabled", "Enabled"], (3 * WIDTH // 4, 340), width=160, index=1)

    # ---------- main loop ----------
    async def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 1 / 30)   # cap dt so lag can't teleport the ball
            for event in pygame.event.get():
                self.handle_event(event)
            if self.state == "game":
                self.update_game(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)
        pygame.quit()

    # ---------- input ----------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        state = self.state
        if state == "menu":
            if self.start_btn.clicked(event):
                self.state = "setup"
            elif self.controls_btn.clicked(event):
                self.state = "controls"
            elif self.exit_btn.clicked(event):
                self.running = False
        elif state == "setup":
            self.difficulty.handle_event(event)
            self.flips.handle_event(event)
            if self.back_btn.clicked(event):
                self.state = "menu"
            elif self.play_btn.clicked(event):
                self.game = logic.Game(self.difficulty.value, self.flips.value == "Enabled")
                self.state = "game"
        elif state == "controls":
            if self.back_btn.clicked(event):
                self.state = "menu"
        elif state == "game":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
        elif state == "gameover":
            if self.menu_btn.clicked(event):
                self.state = "menu"

    def update_game(self, dt):
        keys = pygame.key.get_pressed()
        direction = logic.player_direction(
            up=keys[pygame.K_UP] or keys[pygame.K_w],
            down=keys[pygame.K_DOWN] or keys[pygame.K_s],
            left=keys[pygame.K_LEFT] or keys[pygame.K_a],
            right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
            rotated=self.game.rotated,
        )
        self.game.update(dt, direction)
        if self.game.winner:
            self.state = "gameover"

    # ---------- drawing ----------
    def draw(self):
        self.screen.fill(BLACK)
        mouse = pygame.mouse.get_pos()
        getattr(self, "draw_" + self.state)(mouse)

    def text(self, msg, center, font=None, color=WHITE):
        surf = (font or self.font).render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw_menu(self, mouse):
        draw_block_title(self.screen, "Pong", (WIDTH // 2, 200))
        for btn in (self.start_btn, self.controls_btn, self.exit_btn):
            btn.draw(self.screen, self.font, mouse)

    def draw_setup(self, mouse):
        self.text("Game Setup", (WIDTH // 2, 100), self.big)
        self.difficulty.draw(self.screen, self.font, self.small)
        self.flips.draw(self.screen, self.font, self.small)
        self.back_btn.draw(self.screen, self.font, mouse)
        self.play_btn.draw(self.screen, self.font, mouse)

    def draw_controls(self, mouse):
        self.text("Controls", (WIDTH // 2, 100), self.big)
        lines = [
            ("Move paddle", "Up / Down arrows  or  W / S"),
            ("After a 90° flip", "Left / Right arrows  or  A / D"),
            ("Back to menu", "Esc"),
        ]
        y = 220
        for title, keys in lines:
            self.text(title, (WIDTH // 2, y), color=RED_HOVER)
            self.text(keys, (WIDTH // 2, y + 36), self.small)
            y += 110
        self.text("Your paddle is white. The computer's is red.", (WIDTH // 2, y + 10), self.small, GREY)
        self.back_btn.draw(self.screen, self.font, mouse)

    def draw_game(self, mouse):
        g = self.game
        self.text(f"YOU  {g.player_score}   -   {g.computer_score}  CPU", (WIDTH // 2, 45))
        status = f"{g.difficulty}  |  flips {'on' if g.flips_enabled else 'off'}  |  Esc: menu"
        self.text(status, (WIDTH // 2, 80), self.small, GREY)

        field = pygame.Rect(FIELD_LEFT, FIELD_TOP, logic.FIELD, logic.FIELD)
        pygame.draw.rect(self.screen, GREY, field, 2)

        # Dashed net down the logical middle, transformed like everything else.
        for y in range(0, logic.FIELD, 30):
            self.fill_logical(logic.FIELD / 2, y + 8, 3, 16, GREY)

        self.fill_logical(g.player.x, g.player.y, logic.PADDLE_THICK, logic.PADDLE_LEN, WHITE)
        self.fill_logical(g.computer.x, g.computer.y, logic.PADDLE_THICK, logic.PADDLE_LEN, RED_HOVER)
        self.fill_logical(g.ball.x, g.ball.y, logic.BALL_SIZE, logic.BALL_SIZE, WHITE)

        if g.warning > 0:
            kind = "ROTATE" if g.pending_flip == "rotate" else "SWAP"
            self.text(f"FLIP INCOMING: {kind}!", field.center, self.big, RED_HOVER)
        if g.rotated:
            self.text("Use LEFT / RIGHT (A / D)", (WIDTH // 2, HEIGHT - 10), self.small, RED_HOVER)

    def fill_logical(self, cx, cy, w, h, color):
        """Draw a logical-frame rectangle at its flipped on-screen position."""
        left, top, sw, sh = logic.rect_to_screen(cx, cy, w, h, self.game.rotated, self.game.swapped)
        pygame.draw.rect(self.screen, color, (FIELD_LEFT + left, FIELD_TOP + top, sw, sh))

    def draw_gameover(self, mouse):
        g = self.game
        msg = "YOU WIN!" if g.winner == "player" else "CPU WINS"
        self.text(msg, (WIDTH // 2, 260), self.big, RED_HOVER)
        self.text(f"{g.player_score}  -  {g.computer_score}", (WIDTH // 2, 340))
        self.menu_btn.draw(self.screen, self.font, mouse)


async def main():
    await App().run()


asyncio.run(main())
