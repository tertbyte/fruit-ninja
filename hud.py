"""On-screen text: score/lives HUD, combo banners, start and game-over screens."""

import cv2

from game import Game

_LIFE_FULL = (60, 60, 230)
_LIFE_EMPTY = (75, 75, 75)


def _outlined_text(frame, text, org, scale, color, thickness=2) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_DUPLEX, scale, (0, 0, 0),
                thickness + 4, cv2.LINE_AA)
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_DUPLEX, scale, color,
                thickness, cv2.LINE_AA)


def _centered(frame, text, cy, scale, color, thickness=2) -> None:
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, thickness)
    cx = frame.shape[1] // 2 - tw // 2
    _outlined_text(frame, text, (cx, cy), scale, color, thickness)


def draw_hud(frame, game: Game, now: float) -> None:
    _outlined_text(frame, str(game.score), (24, 55), 1.6, (0, 210, 255), 3)
    _outlined_text(frame, f"BEST {game.best}", (24, 90), 0.7, (0, 210, 255), 1)

    width = frame.shape[1]
    for i in range(3):
        cx = width - 30 - i * 34
        color = _LIFE_FULL if i < game.lives else _LIFE_EMPTY
        cv2.drawMarker(frame, (cx, 32), color, cv2.MARKER_TILTED_CROSS, 22, 4, cv2.LINE_AA)

    for banner in game.banners:
        age = now - banner.born_at
        fade = max(0.0, 1.0 - age / 1.0)
        scale = 1.1 + 0.15 * min(1.0, age * 6)
        cy = int(frame.shape[0] * 0.32 - age * 30)
        color = (int(40 * fade), int(215 * fade + 20), int(255 * fade + 20))
        _centered(frame, banner.text, cy, scale, color, 2)


def _dim(frame, strength: float) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
    cv2.addWeighted(overlay, strength, frame, 1 - strength, 0, frame)


def draw_start_screen(frame) -> None:
    _dim(frame, 0.45)
    h = frame.shape[0]
    _centered(frame, "FRUIT NINJA", h // 2 - 40, 2.2, (0, 210, 255), 4)
    _centered(frame, "Raise your hand(s) and press SPACE to start", h // 2 + 30, 0.8, (255, 255, 255), 2)
    _centered(frame, "Swipe fast through fruit to slice -- avoid the bombs!", h // 2 + 70, 0.7, (200, 200, 200), 1)


def draw_game_over(frame, game: Game) -> None:
    _dim(frame, 0.6)
    h = frame.shape[0]
    _centered(frame, "GAME OVER", h // 2 - 40, 2.0, (0, 60, 255), 4)
    _centered(frame, f"Score: {game.score}   Best: {game.best}", h // 2 + 20, 0.9, (255, 255, 255), 2)
    _centered(frame, "Press SPACE to play again, q to quit", h // 2 + 60, 0.7, (200, 200, 200), 1)
