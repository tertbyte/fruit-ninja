"""Wave spawner: launches fruit, and the occasional bomb, from off the bottom edge.

Difficulty ramps with score (shorter gaps between waves, faster launches,
more fruit per wave) and bombs show up roughly once every six fruit,
matching classic Fruit Ninja's spawn rate.
"""

import random
import time
from typing import List

from entities import Fruit, spawn_fruit
from sprites import FRUIT_KINDS

_BASE_INTERVAL = 1.35
_MIN_INTERVAL = 0.55
_BOMB_AFTER_FRUIT = 6
_BOMB_CHANCE = 0.35


class Spawner:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._next_wave_at = time.monotonic() + 1.2
        self._fruit_since_bomb = 0

    def _interval(self, score: int) -> float:
        return max(_MIN_INTERVAL, _BASE_INTERVAL - score * 0.01)

    def _speed_mult(self, score: int) -> float:
        return min(1.5, 1.0 + score * 0.004)

    def maybe_spawn(self, score: int, now: float) -> List[Fruit]:
        if now < self._next_wave_at:
            return []
        self._next_wave_at = now + self._interval(score)

        max_wave = 1 + min(3, score // 40)
        wave_size = random.randint(1, max_wave)
        speed_mult = self._speed_mult(score)

        spawned = []
        for _ in range(wave_size):
            self._fruit_since_bomb += 1
            spawn_bomb = (self._fruit_since_bomb >= _BOMB_AFTER_FRUIT
                          and random.random() < _BOMB_CHANCE)
            if spawn_bomb:
                self._fruit_since_bomb = 0
                radius = random.randint(30, 38)
                spawned.append(spawn_fruit("bomb", self.width, self.height,
                                            radius, speed_mult, is_bomb=True))
            else:
                kind = random.choice(FRUIT_KINDS)
                radius = random.randint(34, 52)
                spawned.append(spawn_fruit(kind, self.width, self.height,
                                            radius, speed_mult))
        return spawned
