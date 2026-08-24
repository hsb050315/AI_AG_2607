---
name: typecast-tts
description: Generates speech audio (WAV/MP3) from text using the Typecast TTS API, defaulting to the "서현 (Announcer)" voice. Use this skill when the user asks to convert text to speech, generate a voice/audio clip, or narrate text with a specific Typecast character. Requires a TYPECAST_API_KEY environment variable set by the user — this skill never handles the raw key value directly.
---

# typecast-tts: Text-to-Speech via Typecast API

Converts text into spoken audio using the Typecast REST API (`https://api.typecast.ai/v1/text-to-speech`). Always call the bundled `scripts/typecast_tts.py` helper instead of writing raw HTTP requests from scratch.

## Prerequisites

- The user must set a `TYPECAST_API_KEY` environment variable themselves, containing their Typecast API key (issued from Typecast Studio → Developer Tools → API → API Key).
- **Never ask the user to paste the key into chat, and never type/view the raw key value.** If the variable is missing, tell the user how to set it (see "Setting the API key" below) and wait — do not proceed without it.

## Default voice

Unless the user specifies a different character, use:

- **Name:** 서현 (Announcer)
- **voice_id:** `tc_69f2e455ea79fd197aa0476f`

To use a different voice, the user can browse voices at `https://studio.typecast.ai/developers/api/voices` or ask Claude to look one up, then pass its `voice_id` instead.

## Script usage

```python
import sys
sys.path.insert(0, "<this skill folder>/scripts")
from typecast_tts import generate_speech

output_path = generate_speech(
    text="안녕하세요, 타입캐스트 테스트입니다.",
    voice_id="tc_69f2e455ea79fd197aa0476f",  # 서현 (Announcer), default
    output_path="output/audio/sample.wav",     # any path; parent dirs are created automatically
    audio_format="wav",                          # "wav" or "mp3"
)
print(output_path)
```

`generate_speech(text, voice_id=DEFAULT_VOICE_ID, output_path=None, model="ssfm-v30", language=None, audio_format="wav", emotion_preset=None, emotion_intensity=None, audio_pitch=None, audio_tempo=None)`

- `text` — required, 1–2000 characters.
- `voice_id` — defaults to 서현. `tc_` prefix = built-in voice, `uc_` prefix = user-cloned voice.
- `output_path` — where to save the audio file. If omitted, saves to a temp file and returns its path. Per this project's output conventions, save generated audio under `output/audio/`.
- `model` — `ssfm-v30` (default, recommended) or `ssfm-v21`.
- `language` — ISO 639-3 code (`kor`, `eng`, `jpn`, `zho`, ...); auto-detected if omitted.
- `emotion_preset` — one of `normal, happy, sad, angry, whisper, toneup, tonedown`.
- `emotion_intensity` — 0.0–2.0, used with `emotion_preset`.
- `audio_pitch` — -12 to 12 semitones.
- `audio_tempo` — 0.5–2.0 (playback speed).

The function raises a clear exception with the HTTP status and response body on failure — surface that message to the user rather than retrying blindly.

## Setting the API key

The recommended way: the user creates a `.env` file at the repo root themselves (already covered by `.gitignore`) containing one line:

```
TYPECAST_API_KEY=...
```

`scripts/typecast_tts.py` auto-loads this file via `python-dotenv` on import, so it works regardless of which shell/process runs the script — no need to re-set an environment variable in every new terminal session. Setting `$env:TYPECAST_API_KEY = "..."` in a PowerShell session also works, but only for that specific session/process.

Claude should never fill in the actual key value in the `.env` file or anywhere else — the user must type/paste it themselves.

## Error codes

| Code | Meaning |
|------|---------|
| 400 | Invalid parameters |
| 401 | Invalid/missing API key |
| 402 | Insufficient credits |
| 403 | Forbidden (legacy key, dormant account, permission issue) |
| 404 | Voice/model not found |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Server error |

## What not to do

- Do not hardcode an API key anywhere in the script or in chat.
- Do not commit generated `.env` files or audio output containing sensitive user text.
- Do not write raw `requests.post(...)` calls inline — always go through `scripts/typecast_tts.py`.
