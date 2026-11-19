# Fruit Ninja (MediaPipe)

Slice fruit out of thin air with your bare hands. A webcam tracks up to
two hands in real time and turns fast finger swipes into glowing ninja
blades, played right on top of your live camera feed.

## How it works

Each frame from the webcam runs through a short pipeline:

1. **Hand tracking** (`hand_sensor.py`) -- MediaPipe's `HandLandmarker`
   returns 21 3D landmarks per hand; the index fingertip of each hand
   (up to two) becomes a blade tip.
2. **Blade trails** (`blade.py`) -- each hand keeps a short trail of
   recent fingertip points. A pair of consecutive points only counts as
   a "slice segment" once it's moving fast enough, so a hand resting in
   frame doesn't slice everything it touches.
3. **Physics** (`entities.py`) -- fruit and bombs launch from the
   bottom of the frame on a projectile arc (gravity pulls them back
   down) with a bit of spin. A slice segment that passes within a
   fruit's radius marks it sliced; sliced fruit splits into two halves
   that drift apart.
4. **Spawning** (`spawner.py`) -- waves get faster, launch harder, and
   throw more fruit at once as your score climbs. Bombs show up roughly
   once every six fruit.
5. **Rules** (`game.py`) -- see below.
6. **Art** (`sprites.py`) -- fruit/bomb sprites are drawn procedurally
   with Pillow on first run and cached as PNGs in `assets/`, so there's
   no external/licensed art to fetch. The background is just your live
   webcam frame -- fruit, bombs, and the HUD are composited on top of
   it every tick.
7. **Blade rendering** (`main.py`) -- each hand's trail is drawn twice:
   once as a thick, Gaussian-blurred glow layer additively blended onto
   the frame, then again as a thinner bright core on top. Hand 1 glows
   cyan, hand 2 glows magenta, so the blades stay readable against any
   background and distinguishable from each other.

## Rules (matches classic Fruit Ninja)

- **3 lives**, shown as X marks top-right. Letting a fruit fall
  unsliced costs one life.
- **Bombs are instant game over** -- slicing one ends the run no matter
  how many lives you have left.
- **Combos**: slice 3 or more fruit in one swipe and that swipe's score
  *doubles* (shown as a "N FRUIT COMBO +bonus" banner). A "swipe" here
  is approximated as any run of slices with under ~0.45s of idle time
  between them, since the game doesn't segment individual physical
  swipe motions.
- **Life regen**: every time your score crosses a new multiple of 100,
  you regain a life (capped at 3).
- Your best score persists across runs in `best_score.json`.

## Tech

- **Python 3.9+**
- **MediaPipe** (Tasks API -- `HandLandmarker`) for two-hand tracking
- **OpenCV** for webcam I/O, physics-driven sprite compositing, and the HUD
- **Pillow** + **NumPy** for one-time procedural art generation

The hand-landmarker model (`hand_landmarker.task`, ~7 MB) downloads
automatically the first time you run the app and is cached next to the
source, same as the model-download pattern in `air-draw`.

## Install & run

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On macOS, the first launch will prompt for camera access -- approve it,
then re-run.

## Controls

| Input                        | What it does                          |
| ----------------------------- | -------------------------------------- |
| Swipe index finger fast       | Slice any fruit/bomb the blade crosses |
| One or both hands             | Each hand slices independently         |
| `SPACE`                       | Start the game / restart after game over |
| `q`                            | Quit                                   |

## Project layout

```
fruit-ninja-mediapipe/
├── main.py           # webcam loop, owns the cv2 window
├── hand_sensor.py     # MediaPipe wrapper -> fingertip positions per hand
├── blade.py           # per-hand trail -> speed-gated slice segments
├── entities.py        # Fruit/bomb projectile physics
├── spawner.py         # wave timing + difficulty ramp + bomb rate
├── game.py            # score, lives, combo, best-score persistence
├── hud.py             # HUD text, start screen, game-over screen
├── sprites.py         # procedural fruit/bomb art + overlay blit
├── requirements.txt
├── assets/            # generated on first run, git-ignored
└── hand_landmarker.task  # downloaded on first run, git-ignored
```

## Tuning

- Difficulty ramp (wave interval, launch speed, wave size):
  `_BASE_INTERVAL` / `_MIN_INTERVAL` / `_speed_mult` in `spawner.py`
- Bomb frequency: `_BOMB_AFTER_FRUIT` / `_BOMB_CHANCE` in `spawner.py`
- Combo window / lives cap: `_COMBO_WINDOW` / `_MAX_LIVES` in `game.py`
- Minimum swipe speed to register a slice: `_MIN_SLICE_SPEED` in `blade.py`
- Fruit colors/patterns: `_SPECS` in `sprites.py`
- Blade glow colors / softness: `_HAND_GLOW_COLORS` / `_GLOW_BLUR_SIGMA`
  in `main.py`
