import sounddevice as sd
import soundfile as sf

class AudioManager:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

    def play_audio(self, file_path: str):
        """
        Plays an audio file.
        """
        data, fs = sf.read(file_path, dtype='float32')
        sd.play(data, fs)
        sd.wait()

    def record_audio(self, duration: int, file_path: str):
        """
        Records audio for a given duration and saves it to a file.
        """
        print("Recording...")
        recording = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        sf.write(file_path, recording, self.sample_rate)
        print(f"Recording saved to {file_path}")
