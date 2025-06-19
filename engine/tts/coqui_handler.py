from TTS.api import TTS

class CoquiHandler:
    def __init__(self, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        """
        Initializes the Coqui TTS model.
        """
        self.tts = TTS(model_name)

    def synthesize(self, text: str, output_path: str):
        """
        Synthesizes text to speech and saves it to a file.
        """
        self.tts.tts_to_file(text=text, file_path=output_path)
