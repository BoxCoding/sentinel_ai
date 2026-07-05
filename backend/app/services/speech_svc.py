"""Speech-to-Text (emergency call transcription) and Text-to-Speech
(citizen alert broadcasts)."""
import base64

from app.core.config import settings

DEMO_TRANSCRIPT = (
    "Hello please help, there is a fire in my kitchen and it is spreading to the "
    "second floor. My address is 42 Rosewood Lane, Ward 9. My grandmother is still "
    "upstairs, please send someone fast."
)


class SpeechService:
    def transcribe(self, audio_bytes: bytes, language: str = "en-US") -> dict:
        if settings.DEMO_MODE:
            return {"transcript": DEMO_TRANSCRIPT, "confidence": 0.94, "language": language}
        from google.cloud import speech

        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            language_code=language,
            enable_automatic_punctuation=True,
            model="telephony",  # tuned for emergency-call audio
        )
        response = client.recognize(config=config, audio=speech.RecognitionAudio(content=audio_bytes))
        transcript = " ".join(r.alternatives[0].transcript for r in response.results)
        conf = (sum(r.alternatives[0].confidence for r in response.results)
                / max(len(response.results), 1))
        return {"transcript": transcript, "confidence": conf, "language": language}

    def synthesize(self, text: str, language: str = "en-US") -> bytes:
        if settings.DEMO_MODE:
            return base64.b64encode(f"DEMO_TTS::{text}".encode())
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            ),
            audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3),
        )
        return response.audio_content


speech = SpeechService()
