import math
import numpy as np


class SquareWave:
    def __init__(self, samplerate: int = 48000, volume: int = 1000, freq: int = 880):
        self.volume = volume
        self.sample = 0
        self.freq = freq
        self.samplerate = samplerate
        self.delta = self.freq / self.samplerate

    def generate(self, blocksize: int = 960):
        samples = []
        for t in range(0, blocksize):
            self.sample += self.delta
            self.sample -= math.floor(self.sample)
            samples.append(self.volume if self.sample > 0.5 else 0)
        return np.array(samples).reshape(-1, 1)
