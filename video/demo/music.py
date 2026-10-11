"""Generate a quiet ambient music bed (no samples, no licence): slow minor pad + soft sub, as WAV.

    python video/demo/music.py 140 video/demo/music.wav     (seconds, output path)
"""

import sys
import wave

import numpy as np

RATE = 44100


def pad(seconds: float) -> np.ndarray:
    t = np.arange(int(seconds * RATE)) / RATE
    chords = [(220.00, 261.63, 329.63), (196.00, 246.94, 293.66), (174.61, 220.00, 261.63), (196.00, 233.08, 293.66)]  # Am G F Gm
    out = np.zeros_like(t)
    seg = 8.0  # seconds per chord, with slow crossfades
    for i, chord in enumerate(chords * int(seconds // (seg * len(chords)) + 1)):
        start = i * seg
        env = np.clip(1 - np.abs((t - start - seg / 2) / (seg * 0.75)), 0, 1) ** 2
        for f in chord:
            out += env * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t)) / 3
        out += env * 0.5 * np.sin(2 * np.pi * chord[0] / 2 * t)  # sub
    out *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)  # slow swell
    fade = np.minimum(1, np.minimum(t / 3, (seconds - t) / 4))
    out *= fade
    return out / np.max(np.abs(out)) * 0.9


if __name__ == "__main__":
    seconds, path = float(sys.argv[1]), sys.argv[2]
    data = (pad(seconds) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    print(f"wrote {path} ({seconds:.0f} s)")
