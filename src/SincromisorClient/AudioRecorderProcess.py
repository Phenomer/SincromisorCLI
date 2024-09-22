import time
import numpy as np
from queue import Full
from multiprocessing import Process, Queue
from asyncio import Event
import sounddevice as sd


class AudioRecorderProcess(Process):
    def __init__(
        self,
        voice_queue: Queue,
        channels: int = 1,
        samplerate: int = 48000,
        dtype: str = "int16",
        blocksize=960,
        device: str = "default",
        shutdown_event: Event = Event(),
    ):
        Process.__init__(self)
        self.channels: int = channels
        self.samplerate: int = samplerate
        self.dtype: str = dtype
        self.device: str = device
        self.blocksize: int = blocksize
        self.voice_queue: Queue = voice_queue
        self.shutdown_event: Event = shutdown_event

    def run(self) -> None:
        self.timestamp = 0
        print(
            [
                "AudioRecorder",
                self.channels,
                self.samplerate,
                self.dtype,
                self.blocksize,
                self.device,
            ]
        )
        sound_input = sd.InputStream(
            channels=self.channels,
            samplerate=self.samplerate,
            dtype=self.dtype,
            blocksize=self.blocksize,
            device=self.device,
            callback=self.__recorder_callback,
        )
        sound_input.start()
        print("start AudioRecorder")
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        sound_input.close()
        print("stop AudioRecorder")

    def __recorder_callback(
        self, outdata: np.ndarray, frames: int, time, status: sd.CallbackFlags
    ):
        try:
            # ndarrayをそのまま送ると壊れるのでbytesにする。
            self.voice_queue.put(outdata.tobytes())
        except Full:
            return
        except Exception as e:
            print(e)
            self.shutdown_event.set()
