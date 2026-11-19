"""Fruit Ninja, controlled by your hands via a webcam.

Raise one or both hands into frame and swipe fast across a fruit to
slice it -- MediaPipe tracks each hand's index fingertip as a blade tip.
Fruit and the HUD render directly over your live webcam feed, and each
hand gets its own glowing neon blade trail so the slices stay easy to
spot against a busy background.

Rules:
  * 3 lives (top-right X marks). Missing a fruit costs one; slicing a
    bomb ends the run immediately, no matter how many lives are left.
  * Slice 3+ fruit in one swipe for a combo -- that swipe's score
    doubles.
  * Score crosses a new hundred -> regain a life (capped at 3).

Controls:
  SPACE   start / restart
  q       quit
"""

import math
import sys
import time

import cv2
import numpy as np

from blade import BladeTracker
from game import Game, State
from hand_sensor import HandSensor
from hud import draw_game_over, draw_hud, draw_start_screen
from spawner import Spawner
from sprites import SPRITE_SIZE, load_or_generate, overlay

WINDOW_NAME = "Fruit Ninja"
CAMERA_INDEX = 0
WIDTH, HEIGHT = 1280, 720

# BGR neon colors, one per tracked hand, so simultaneous two-hand slices
# stay visually distinct from each other and from the camera background.
_HAND_GLOW_COLORS = [(255, 255, 0), (255, 0, 255)]
_GLOW_BLUR_SIGMA = 9


def _open_camera() -> cv2.VideoCapture:
    cam = cv2.VideoCapture(CAMERA_INDEX)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    if not cam.isOpened():
        print("Could not open the webcam.", file=sys.stderr)
        sys.exit(1)
    return cam


def _segment_hits_circle(p0, p1, cx, cy, r) -> bool:
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((cx - x0) * dx + (cy - y0) * dy) / length_sq))
    px, py = x0 + t * dx, y0 + t * dy
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def _draw_blade_trails(frame, blade: BladeTracker) -> None:
    """Neon glow trail per hand: a blurred glow layer plus a bright core line."""
    all_points = blade.trail_points()

    glow = np.zeros_like(frame)
    for hand_idx, points in enumerate(all_points):
        color = _HAND_GLOW_COLORS[hand_idx % len(_HAND_GLOW_COLORS)]
        for i in range(1, len(points)):
            thickness = 6 + int(10 * i / len(points))
            cv2.line(glow, points[i - 1], points[i], color, thickness, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), sigmaX=_GLOW_BLUR_SIGMA)
    cv2.add(frame, glow, dst=frame)

    for hand_idx, points in enumerate(all_points):
        color = _HAND_GLOW_COLORS[hand_idx % len(_HAND_GLOW_COLORS)]
        core_color = tuple(min(255, c + 90) for c in color)
        for i in range(1, len(points)):
            thickness = 2 + int(4 * i / len(points))
            cv2.line(frame, points[i - 1], points[i], core_color, thickness, cv2.LINE_AA)


def run() -> None:
    camera = _open_camera()
    ok, first_frame = camera.read()
    if not ok:
        print("Camera returned no frame.", file=sys.stderr)
        sys.exit(1)
    height, width = first_frame.shape[:2]

    fruit_sprites, bomb_sprite = load_or_generate()
    sensor = HandSensor()
    blade = BladeTracker()
    spawner = Spawner(width, height)
    game = Game()
    active = []

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    last_time = time.monotonic()

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fingertips = sensor.read(rgb, width, height)
            segments = blade.update(fingertips)

            now = time.monotonic()
            dt = min(0.05, now - last_time)
            last_time = now

            canvas = frame  # play directly over the live webcam feed

            if game.state == State.PLAYING:
                active.extend(spawner.maybe_spawn(game.score, now))

                for fruit in active:
                    fruit.update(dt)
                    if fruit.sliced:
                        continue
                    for p0, p1 in segments:
                        if _segment_hits_circle(p0, p1, fruit.x, fruit.y, fruit.radius):
                            fruit.slice(now)
                            game.register_slice(fruit.is_bomb, now)
                            break

                for fruit in active:
                    if not fruit.sliced and fruit.offscreen_bottom(height) and not fruit.is_bomb:
                        game.register_miss(now)

                active = [f for f in active if not (
                    (f.sliced and f.half_offset > 260) or
                    (not f.sliced and f.offscreen_bottom(height))
                )]

                game.update(now)

                for fruit in active:
                    scale = (fruit.radius * 2) / SPRITE_SIZE
                    angle_deg = math.degrees(fruit.angle)
                    if fruit.is_bomb:
                        if not fruit.sliced:
                            overlay(canvas, bomb_sprite, fruit.x, fruit.y, angle_deg, scale)
                        continue
                    sprite_set = fruit_sprites[fruit.kind]
                    if not fruit.sliced:
                        overlay(canvas, sprite_set["whole"], fruit.x, fruit.y, angle_deg, scale)
                    else:
                        drift = fruit.half_offset
                        overlay(canvas, sprite_set["left"], fruit.x - drift * 0.5,
                                fruit.y + drift * 0.35, angle_deg - 12, scale)
                        overlay(canvas, sprite_set["right"], fruit.x + drift * 0.5,
                                fruit.y + drift * 0.35, angle_deg + 12, scale)

                _draw_blade_trails(canvas, blade)
                draw_hud(canvas, game, now)

            elif game.state == State.READY:
                draw_start_screen(canvas)
            else:
                draw_game_over(canvas, game)

            cv2.imshow(WINDOW_NAME, canvas)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord(" ") and game.state != State.PLAYING:
                active = []
                spawner = Spawner(width, height)
                game.start()

    finally:
        sensor.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
