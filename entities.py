"""Physics for fruit and bombs launched from the bottom of the frame.

Every object follows a simple projectile arc (constant gravity) so it
rises into frame, arcs, and falls back down if nobody slices it. Once
sliced, a fruit's two halves drift apart and away under a small amount
of extra "explosion" velocity for a satisfying split.
"""

import random
from dataclasses import dataclass

GRAVITY = 1400.0  # px/s^2


@dataclass
class Fruit:
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    radius: int
    spin: float
    is_bomb: bool = False
    angle: float = 0.0
    sliced: bool = False
    sliced_at: float = 0.0
    half_offset: float = 0.0

    def update(self, dt: float) -> None:
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        if self.sliced:
            self.half_offset += 260.0 * dt

    def offscreen_bottom(self, height: int) -> bool:
        return self.y - self.radius > height + 40

    def slice(self, now: float) -> None:
        self.sliced = True
        self.sliced_at = now


def spawn_fruit(kind: str, width: int, height: int, radius: int,
                speed_mult: float, is_bomb: bool = False) -> Fruit:
    x = random.uniform(width * 0.15, width * 0.85)
    vx = random.uniform(-140.0, 140.0)
    vy = random.uniform(-1450.0, -1150.0) * speed_mult
    spin = random.uniform(-4.0, 4.0)
    return Fruit(kind=kind, x=x, y=height + radius, vx=vx, vy=vy,
                 radius=radius, spin=spin, is_bomb=is_bomb)
