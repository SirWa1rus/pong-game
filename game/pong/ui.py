"""Reusable pygame widgets: buttons, discrete sliders, and the block title."""

import colorsys

import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (120, 120, 120)


def hsv_color(h, s, v):
    """Build an RGB tuple (0-255) from hue/saturation/value in 0-1."""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return round(r * 255), round(g * 255), round(b * 255)


# Same red hue and brightness; hovering only raises the saturation.
RED = hsv_color(0.0, 0.60, 0.85)
RED_HOVER = hsv_color(0.0, 1.00, 0.85)


class Button:
    """A red button with white text that gets more saturated on hover."""

    def __init__(self, text, center, size=(220, 56)):
        self.text = text
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface, font, mouse_pos):
        color = RED_HOVER if self.hovered(mouse_pos) else RED
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        label = font.render(self.text, True, WHITE)
        surface.blit(label, label.get_rect(center=self.rect.center))


class Slider:
    """A horizontal slider that snaps to a fixed list of options.

    Click anywhere on the track or drag the knob to choose.
    """

    def __init__(self, label, options, center, width=220, index=0):
        self.label = label
        self.options = list(options)
        self.index = index
        self.track = pygame.Rect(0, 0, width, 6)
        self.track.center = center
        self.dragging = False

    @property
    def value(self):
        return self.options[self.index]

    def _stop_x(self, i):
        if len(self.options) == 1:
            return self.track.centerx
        return self.track.left + self.track.width * i / (len(self.options) - 1)

    def _pick(self, x):
        # Choose the stop closest to the mouse.
        self.index = min(range(len(self.options)), key=lambda i: abs(self._stop_x(i) - x))

    def handle_event(self, event):
        hit_area = self.track.inflate(30, 40)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hit_area.collidepoint(event.pos):
            self.dragging = True
            self._pick(event.pos[0])
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._pick(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

    def draw(self, surface, font, small_font):
        title = font.render(self.label, True, WHITE)
        surface.blit(title, title.get_rect(midbottom=(self.track.centerx, self.track.top - 50)))

        current = font.render(self.value, True, RED_HOVER)
        surface.blit(current, current.get_rect(midbottom=(self.track.centerx, self.track.top - 18)))

        pygame.draw.rect(surface, GREY, self.track, border_radius=3)
        for i, option in enumerate(self.options):
            x = self._stop_x(i)
            pygame.draw.line(surface, WHITE, (x, self.track.top - 6), (x, self.track.bottom + 6), 2)
            tick = small_font.render(option, True, GREY)
            surface.blit(tick, tick.get_rect(midtop=(x, self.track.bottom + 12)))

        knob = (round(self._stop_x(self.index)), self.track.centery)
        pygame.draw.circle(surface, RED_HOVER if self.dragging else RED, knob, 13)
        pygame.draw.circle(surface, WHITE, knob, 13, 2)


# 5x5 bitmaps for the block-letter title. '#' = filled block.
BLOCK_LETTERS = {
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "G": [".####", "#....", "#..##", "#...#", ".###."],
}


def draw_block_title(surface, text, center, block=16, color=WHITE):
    """Draw `text` in big square-block letters, centered on `center`."""
    letters = [BLOCK_LETTERS[ch] for ch in text.upper()]
    gap = block
    width = len(letters) * 5 * block + (len(letters) - 1) * gap
    left = center[0] - width // 2
    top = center[1] - (5 * block) // 2
    for n, rows in enumerate(letters):
        x0 = left + n * (5 * block + gap)
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell == "#":
                    pygame.draw.rect(surface, color,
                                     (x0 + c * block, top + r * block, block - 2, block - 2))
