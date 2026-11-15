import asyncio
import io

from config import AZURE_SPEECH_KEY, AZURE_SPEECH_LANGUAGE, AZURE_SPEECH_REGION


class SpeechServiceUnavailable(RuntimeError):
    """Azure Speech is not configured or could not process the audio."""


def _speech_sdk():
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as exc:
        raise SpeechServiceUnavailable(
            "Azure Speech SDK is not installed"
        ) from exc
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        raise SpeechServiceUnavailable(
            "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are required"
        )
    return speechsdk


def _transcribe_sync(audio_bytes: bytes) -> str:
    speechsdk = _speech_sdk()
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )
    speech_config.speech_recognition_language = AZURE_SPEECH_LANGUAGE
    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=16000,
        bits_per_sample=16,
        channels=1,
    )
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format)
    push_stream.write(audio_bytes)
    push_stream.close()
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    result = recognizer.recognize_once_async().get()
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return ""
    return result.text.strip()


def _synthesize_sync(text: str) -> bytes:
    speechsdk = _speech_sdk()
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None,
    )
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise SpeechServiceUnavailable("Azure Speech synthesis failed")
    stream = speechsdk.AudioDataStream(result)
    output = io.BytesIO()
    buffer = bytearray(4096)
    while True:
        read = stream.read_data(buffer)
        if not read:
            break
        output.write(buffer[:read])
    return output.getvalue()


async def transcribe(audio_bytes: bytes) -> str:
    return await asyncio.to_thread(_transcribe_sync, audio_bytes)


async def synthesize(text: str) -> bytes:
    return await asyncio.to_thread(_synthesize_sync, text)
