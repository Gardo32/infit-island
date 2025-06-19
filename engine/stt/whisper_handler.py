import whisper

class WhisperHandler:
    def __init__(self, model_size="base"):
        """
        Initializes the Whisper model.
        """
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes an audio file to text.
        """
        result = self.model.transcribe(audio_file_path)
        return result["text"]
