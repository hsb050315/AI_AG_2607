"""Typecast TTS API helper.

Calls https://api.typecast.ai/v1/text-to-speech using the TYPECAST_API_KEY
environment variable. See SKILL.md in the parent folder for usage.
"""

import os
import tempfile

import requests

API_URL = "https://api.typecast.ai/v1/text-to-speech"
DEFAULT_VOICE_ID = "tc_69f2e455ea79fd197aa0476f"  # 서현 (Announcer)
DEFAULT_MODEL = "ssfm-v30"


def generate_speech(
    text,
    voice_id=DEFAULT_VOICE_ID,
    output_path=None,
    model=DEFAULT_MODEL,
    language=None,
    audio_format="wav",
    emotion_preset=None,
    emotion_intensity=None,
    audio_pitch=None,
    audio_tempo=None,
):
    """Generate speech audio from text and save it to a file.

    Returns the path to the saved audio file.
    Raises RuntimeError with the HTTP status and response body on failure.
    """
    api_key = os.environ.get("TYPECAST_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TYPECAST_API_KEY environment variable is not set. "
            "The user must set it themselves before this can run."
        )

    if not text or len(text) > 2000:
        raise ValueError("text must be 1 to 2000 characters long")

    body = {
        "voice_id": voice_id,
        "text": text,
        "model": model,
        "output": {"audio_format": audio_format},
    }
    if language:
        body["language"] = language
    if audio_pitch is not None:
        body["output"]["audio_pitch"] = audio_pitch
    if audio_tempo is not None:
        body["output"]["audio_tempo"] = audio_tempo
    if emotion_preset:
        body["prompt"] = {
            "emotion_type": "preset",
            "emotion_preset": emotion_preset,
        }
        if emotion_intensity is not None:
            body["prompt"]["emotion_intensity"] = emotion_intensity

    response = requests.post(
        API_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Typecast API request failed: HTTP {response.status_code} - {response.text}"
        )

    if output_path is None:
        suffix = ".wav" if audio_format == "wav" else ".mp3"
        fd, output_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
    else:
        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
