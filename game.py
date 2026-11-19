"""Game state machine: score, lives, combos, and the win/lose rules.

Rules (matching classic Fruit Ninja):
  * 3 lives; letting a (non-bomb) fruit fall unsliced costs one.
  * Slicing a bomb ends the run immediately, regardless of lives left.
  * Slicing 3+ fruit in one swipe is a combo -- that swipe's score
    doubles. A swipe is approximated as any run of slices with no more
    than `_COMBO_WINDOW` seconds of idle time between them, since we
    don't segment individual physical swipes.
  * A life is regained (up to the 3-life cap) each time score crosses
    a new multiple of 100.
"""

import json
import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import List

_BEST_SCORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best_score.json")
_MAX_LIVES = 3
_COMBO_WINDOW = 0.45


class State(Enum):
    READY = auto()
    PLAYING = auto()
    GAME_OVER = auto()


@dataclass
class ComboBanner:
    text: str
    born_at: float


class Game:
    def __init__(self):
        self.state = State.READY
        self.score = 0
        self.lives = _MAX_LIVES
        self.best = self._load_best()
        self.banners: List[ComboBanner] = []
        self._combo_count = 0
        self._combo_deadline = 0.0

    def _load_best(self) -> int:
        try:
            with open(_BEST_SCORE_PATH) as f:
                return int(json.load(f).get("best", 0))
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return 0

    def _save_best(self) -> None:
        with open(_BEST_SCORE_PATH, "w") as f:
            json.dump({"best": self.best}, f)

    def start(self) -> None:
        self.state = State.PLAYING
        self.score = 0
        self.lives = _MAX_LIVES
        self._combo_count = 0
        self.banners.clear()

    def register_slice(self, is_bomb: bool, now: float) -> None:
        if self.state != State.PLAYING:
            return
        if is_bomb:
            self._finish_combo(now)
            self._end_game()
            return
        self._combo_count += 1
        self._combo_deadline = now + _COMBO_WINDOW

    def register_miss(self, now: float) -> None:
        if self.state != State.PLAYING:
            return
        self._finish_combo(now)
        self.lives -= 1
        if self.lives <= 0:
            self._end_game()

    def update(self, now: float) -> None:
        if self.state == State.PLAYING and self._combo_count and now >= self._combo_deadline:
            self._finish_combo(now)
        self.banners = [b for b in self.banners if now - b.born_at < 1.0]

    def _finish_combo(self, now: float) -> None:
        count = self._combo_count
        self._combo_count = 0
        if count == 0:
            return
        gained = count
        if count >= 3:
            gained *= 2
            self.banners.append(ComboBanner(f"{count} FRUIT COMBO +{gained - count}", now))
        self._add_score(gained)

    def _add_score(self, amount: int) -> None:
        prev_tier = self.score // 100
        self.score += amount
        self.best = max(self.best, self.score)
        new_tier = self.score // 100
        if new_tier > prev_tier and self.lives < _MAX_LIVES:
            self.lives += 1

    def _end_game(self) -> None:
        self.state = State.GAME_OVER
        self._save_best()
