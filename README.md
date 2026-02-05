# AIOC Ham Radio Voice Chatbot

An AI-powered voice chatbot for amateur radio. Listens on 2m FM, transcribes
incoming transmissions, generates conversational responses with a local LLM,
and speaks them back over the air in the operator's cloned voice. Fully
offline-capable, FCC Part 97 compliant.

**Station callsign: AK6MJ**

## How It Works

```
            Baofeng HT ─── AIOC USB cable ─── Mac (Apple Silicon)
                                                  │
    Incoming          ┌───────────────────────────┘
    transmission      ▼
    over FM ───► VOX detect ──► Whisper STT ──► Ollama LLM ──► Content filter
                                                     │              │
                                                 (web search        │
                                                  if needed)        ▼
                                                              Qwen3-TTS
                                                           (cloned voice)
                                                                │
                                                                ▼
                                                           PTT + transmit
```

The pipeline is single-threaded and blocking — this matches the half-duplex
nature of FM radio. The bot keys the transmitter via serial DTR/RTS through
the AIOC cable, speaks, then unkeys and resumes listening.

## Hardware

- **Radio**: Baofeng (or any HT with a Kenwood-style 2-pin connector)
- **Interface**: [AIOC (All-In-One Cable)](https://github.com/skuep/AIOC) — USB
  sound card + serial PTT in a single cable (VID `1209`, PID `7388`)
- **Computer**: Mac with Apple Silicon (M1/M2/M3/M4) and 32GB+ RAM
  - The LLM (qwen3:32b) benefits from 64GB+; smaller models work with less

## Software Stack

| Component | Library | Notes |
|-----------|---------|-------|
| **STT** | [lightning-whisper-mlx](https://github.com/mustafaaljadery/lightning-whisper-mlx) | `distil-medium.en`, optimized for Apple Silicon |
| **LLM** | [Ollama](https://ollama.com) | `qwen3:32b` running locally |
| **TTS** | [mlx-audio](https://github.com/lucasnewman/mlx-audio) (Qwen3-TTS) | Voice-cloned output using a reference audio profile |
| **Web search** | [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | Triggered automatically for factual questions |
| **Audio I/O** | [sounddevice](https://python-sounddevice.readthedocs.io/) | PortAudio bindings |
| **PTT** | [pyserial](https://pyserial.readthedocs.io/) | DTR/RTS control over AIOC serial |

## Prerequisites

- macOS on Apple Silicon
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- [Ollama](https://ollama.com) installed and running
- AIOC cable (for live radio; not needed for dry-run mode)
- A voice profile directory with `audio.wav` and `meta.json` (see **Voice Clone** below)

## Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd aioc-bot

# 2. Create the conda environment and install dependencies
make setup

# 3. Pull the LLM model
ollama pull qwen3:32b

# 4. (Optional) Pull a smaller model if RAM is limited
# ollama pull qwen3:8b
# Then edit config.yaml: llm.model: "qwen3:8b"
```

## Usage

```bash
# Start Ollama (if not already running)
ollama serve

# Run with AIOC hardware attached
make run

# Run in dry-run mode (system mic + speakers, no PTT)
make dry-run

# Calibrate VOX threshold (shows live audio levels)
make monitor
```

### Command-line options

```
python main.py              # Normal operation (requires AIOC)
python main.py --dry-run    # Uses system mic/speakers, no PTT
python main.py --monitor    # Shows live audio levels, then exits
python main.py --log-level DEBUG   # Verbose logging
python main.py -c custom.yaml     # Use alternate config file
```

### Shutting down

- **Ctrl+C** — graceful shutdown (transmits a sign-off ID, then exits)
- **Ctrl+C twice** — force quit
- **Over the air** — say "*AK6MJ shut down*" or "*AK6MJ go silent*"

## Configuration

All settings are in `config.yaml`:

```yaml
callsign: "AK6MJ"
id_interval_sec: 600         # Station ID every 10 minutes (FCC §97.119)

aioc:
  serial_port: auto          # Auto-detect AIOC, or set path like /dev/cu.usbmodem14301
  audio_device: "AllInOneCable"
  sample_rate: 48000
  channels: 1

vox:
  threshold_dbfs: -47        # Raise if breathing triggers VOX, lower if speech doesn't
  hang_time_sec: 1.0         # Silence duration before ending a recording
  min_transmission_sec: 0.5  # Ignore noise bursts shorter than this
  max_transmission_sec: 120  # Safety cap

llm:
  model: "qwen3:32b"
  max_tokens: 200
  temperature: 0.7

tts:
  speed: 1.0
  tone: 50                   # 0 = formal, 100 = conversational
```

See `config.yaml` for the full file with all options.

## Voice Clone

The TTS system uses Qwen3-TTS with a reference voice profile. The profile
directory (configured as `tts.voice_profile_dir`) must contain:

- `audio.wav` — a short (5-15s) recording of the target voice
- `meta.json` — metadata including a transcript of the audio:
  ```json
  {
    "name": "Your Name",
    "transcript": "Exact transcript of audio.wav content..."
  }
  ```

## FCC Compliance

The bot enforces Part 97 rules automatically:

- **Station ID** (§97.119): Transmits callsign in NATO phonetics every 10 minutes
  and at sign-on/sign-off
- **Content filter** (§97.113, §97.117): Blocks profanity, commercial language,
  URLs, and email addresses from LLM output
- **Emergency traffic**: Detects "mayday", "break break", etc. and goes silent
- **Control operator**: Responds to over-the-air shutdown commands

## Project Structure

```
main.py          Entry point — argument parsing, main loop, transmit logic
audio.py         AIOC hardware interface, VOX recorder, PTT control, audio playback
stt.py           Speech-to-text (lightning-whisper-mlx)
tts.py           Text-to-speech with voice cloning (Qwen3-TTS / mlx-audio)
llm.py           Ollama chat with DuckDuckGo web search augmentation
compliance.py    FCC Part 97 enforcement — station ID, content filter, emergency detect
config.yaml      All runtime configuration
Makefile         Convenience targets (setup, run, dry-run, monitor, clean)
HARDWARE_TEST.md Step-by-step guide for calibrating with real radio hardware
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `AIOC serial port not found` | Check USB cable, try a different port |
| `AIOC audio device not found` | Run `make monitor`, verify "AllInOneCable" appears |
| VOX triggers on noise/breathing | Raise `threshold_dbfs` in config, raise Baofeng squelch |
| VOX never triggers | Lower `threshold_dbfs`, check Baofeng squelch isn't too high |
| First syllable clipped | Increase `time.sleep(0.3)` in `audio.py` `ptt_on()` |
| Response audio distorted | Lower normalize peak in `tts.py` (0.9 to 0.6) |
| Ctrl+C doesn't quit | Hit Ctrl+C a second time to force quit |

See `HARDWARE_TEST.md` for a full calibration walkthrough.

## License

This project is provided as-is for amateur radio experimentation. You are
responsible for complying with your country's amateur radio regulations.
Operation requires a valid amateur radio license.
