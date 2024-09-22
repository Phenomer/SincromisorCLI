from av.audio.frame import AudioFrame
from fractions import Fraction
from .SquareWave import SquareWave


class DummyAudioRecorder:
    def __init__(
        self,
        channels: int = 1,
        samplerate: int = 48000,
        dtype: str = "int16",
        blocksize=960,
        device: str = "default",
    ):
        self.channels = channels
        self.samplerate = samplerate
        self.dtype = dtype
        self.device = device
        self.blocksize = blocksize
        self.timestamp = 0
        self.wave_generator = SquareWave(samplerate=self.samplerate)
        print("start DummyAudioRecorder")

    def get_frame(self):
        frame = AudioFrame.from_ndarray(
            self.wave_generator(self.blocksize), format="s16", layout="mono"
        )
        self.timestamp += frame.samples
        frame.pts = self.timestamp
        frame.time_base = Fraction(1, self.samplerate)
        frame.sample_rate = self.samplerate
        return frame


if __name__ == "__main__":
    import sys

    try:
        ap = DummyAudioRecorder(blocksize=2048)
        while True:
            print(ap.get_frame())
    except KeyboardInterrupt:
        sys.exit(1)
