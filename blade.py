"""Blade trails: turns raw fingertip positions into slice-detecting segments.

Each tracked hand keeps a short trail of recent fingertip points. A pair
of consecutive points becomes a "slice segment" only once it is moving
fast enough -- this is what stops a hand that's just resting in frame
from slicing everything it touches.
"""

import math
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Point = Tuple[int, int]
Segment = Tuple[Point, Point]

_TRAIL_LIFETIME = 0.18   # seconds a point stays part of the visible trail
_MIN_SLICE_SPEED = 500.0  # px/sec; slower motion doesn't count as a slice
_MAX_HANDS = 2


@dataclass
class _Trail:
    points: List[Tuple[Point, float]] = field(default_factory=list)

    def add(self, point: Point, now: float) -> None:
        self.points.append((point, now))
        self._prune(now)

    def decay(self, now: float) -> None:
        self._prune(now)

    def _prune(self, now: float) -> None:
        self.points = [(p, t) for p, t in self.points if now - t <= _TRAIL_LIFETIME]

    def latest_segment(self) -> Optional[Segment]:
        if len(self.points) < 2:
            return None
        (p0, t0), (p1, t1) = self.points[-2], self.points[-1]
        dt = t1 - t0
        if dt <= 0:
            return None
        speed = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / dt
        if speed < _MIN_SLICE_SPEED:
            return None
        return p0, p1


class BladeTracker:
    """Owns one trail per hand and exposes both slicing segments and points to draw."""

    def __init__(self):
        self._trails: List[_Trail] = [_Trail() for _ in range(_MAX_HANDS)]

    def update(self, fingertips: List[Point]) -> List[Segment]:
        now = time.monotonic()
        segments: List[Segment] = []
        for i, trail in enumerate(self._trails):
            if i < len(fingertips):
                trail.add(fingertips[i], now)
                segment = trail.latest_segment()
                if segment is not None:
                    segments.append(segment)
            else:
                trail.decay(now)
        return segments

    def trail_points(self) -> List[List[Point]]:
        """Per-hand list of recent points, oldest first, for rendering."""
        return [[p for p, _ in trail.points] for trail in self._trails]
