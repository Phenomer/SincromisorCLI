import numpy as np
from aiortc import AudioStreamTrack
from multiprocessing import Queue
from queue import Empty
from asyncio import Event
from av.audio.frame import AudioFrame
from fractions import Fraction
from .AudioRecorderProcess import AudioRecorderProcess


class AudioSenderTrack(AudioStreamTrack):
    def __init__(
        self,
        channels: int = 1,
        samplerate: int = 48000,
        dtype: str = "int16",
        blocksize: int = 960,
        device: str = "default",
        shutdown_event: Event = Event(),
    ):
        super().__init__()
        self.shutdown_event: Event = shutdown_event
        self.voice_queue: Queue = Queue(3)
        self.timestamp: int = 0
        self.samplerate: int = samplerate
        self.blocksize: int = blocksize
        print(["AudioSenderTrack", channels, samplerate, dtype, blocksize, device])
        self.audio_p = AudioRecorderProcess(
            voice_queue=self.voice_queue,
            channels=channels,
            samplerate=samplerate,
            dtype=dtype,
            blocksize=blocksize,
            device=device,
            shutdown_event=self.shutdown_event,
        )
        self.audio_p.start()

    # 960ブロック(960 / 480000 = 1/50秒, 20ms)のサンプルを持つフレームを返す。
    # 960以外の値とすると音声が壊れたり、パケットが落とされたりするので注意。
    # モノラルでも自動的に48000Hz/2chにリサンプルされ、opus形式にエンコードさせる。
    # ここで確実にフレームを返しておかないと、aiortc/rtcrtpsender.pyの
    # _next_encoded_frameのawait self.__track.recv()が永遠に待ち続けてしまい、
    # 適切に終了できなくなる。
    async def recv(self):
        try:
            # 0.02秒ごとに1ブロックのサンプルが得られるはずなので、
            # 0.05秒ぐらい待ってダメそうならダミーデータを送る
            byte_frame: bytes = self.voice_queue.get(block=True, timeout=0.05)
        except Empty:
            # 音声データが無い時はダミーのフレームを返す
            byte_frame: bytes = b"\0" * 960 * 2
        except Exception as e:
            print(f"recv_exception {e}")
            byte_frame: bytes = b"\0" * 960 * 2
        np_frame: np.ndarray = np.frombuffer(byte_frame, dtype=np.int16)
        frame = AudioFrame.from_ndarray(
            np_frame.reshape(1, self.blocksize), format="s16", layout="mono"
        )
        self.timestamp += frame.samples
        frame.pts = self.timestamp
        frame.time_base = Fraction(1, self.samplerate)
        frame.sample_rate = self.samplerate
        return frame

    def close(self):
        if not self.shutdown_event.is_set():
            self.shutdown_event.set()
        self.audio_p.close()
        self.voice_queue.close()
