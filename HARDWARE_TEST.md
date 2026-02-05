# AIOC Hardware Test Cheat Sheet

## Setup

```
HT #1 (Baofeng + AIOC) ---USB---> Mac (running aioc-bot)
HT #2 (any handheld)   ---you talk into this one
Both on same simplex freq, low power (1W)
```

## Step 1: Verify AIOC is detected

```bash
# Check serial port
ls /dev/cu.usbmodem*

# Check audio device
make monitor
# Should say "AllInOneCable" not "MacBook Pro Microphone"
```

If it shows Mac mic instead of AIOC, check USB connection.

## Step 2: Calibrate audio levels

```bash
make monitor
```

- Squelch closed (quiet): note the noise floor (probably -70 to -90 dBFS)
- Key HT #2 and talk: note speech levels
- Set `threshold_dbfs` in `config.yaml` halfway between noise floor and speech
- Example: noise = -70, speech = -30, set threshold to -50

## Step 3: Baofeng squelch setting

On the Baofeng connected to AIOC:
- **Menu 0 (SQL)**: Set squelch level 3-5
  - Too low = AIOC hears static, VOX triggers on noise
  - Too high = cuts off weak signals
- Test: with HT #2 off, AIOC should see silence (-70 dBFS or lower)
- Test: key HT #2, AIOC should see speech (-40 to -20 dBFS)

## Step 4: PTT timing

If the first syllable gets clipped, increase PTT settle time in `audio.py`:

```python
# audio.py line ~117
time.sleep(0.3)  # increase to 0.5 or 0.8 if clipping
```

If using a repeater with CTCSS, you may need 0.5-1.0s.

## Step 5: TX audio level

If response audio is too loud/quiet on HT #2:

**Option A: Software (config.yaml)**
```yaml
tts:
  speed: 1.0      # 0.8 = slower/clearer, 1.2 = faster
  tone: 50        # lower = more controlled delivery
```

**Option B: AIOC firmware (one-time config)**
```bash
# Install AIOC config tool (from AIOC GitHub releases)
# Adjust TX audio level:
# Register AUDIO_TX (0x78) — values: 0=mic level, 1=line level
# Most Baofengs want mic level (default)
```

**Option C: Normalize peak in tts.py**
```python
# tts.py ~line 85
audio = audio / peak * 0.9  # lower 0.9 to 0.6 if too hot
```

## Step 6: Run it

```bash
make run
```

Key HT #2, ask a question, wait ~15s for response.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "AIOC serial port not found" | Check USB cable, try different port |
| "AIOC audio device not found" | Run `make monitor`, check device name |
| VOX triggers on noise | Raise squelch on Baofeng (Menu 0), raise `threshold_dbfs` |
| VOX never triggers | Lower `threshold_dbfs`, check squelch isn't muting everything |
| First syllable clipped | Increase `time.sleep(0.3)` in `audio.py` ptt_on |
| Audio too loud/distorted | Lower normalize peak in tts.py (0.9 → 0.6) |
| Audio too quiet | Raise normalize peak, or lower Baofeng squelch on HT #2 |
| Bot hears itself | Only happens in dry-run (speakers + mic). Not an issue with AIOC since radio is half-duplex |
| Ctrl+C doesn't quit | Hit Ctrl+C twice (second one force-quits) |

## Config quick reference (config.yaml)

```yaml
# Most likely to need tuning:
vox:
  threshold_dbfs: -47   # raise if breathing triggers, lower if speech doesn't
  hang_time_sec: 1.0    # raise if it cuts off mid-sentence
  min_transmission_sec: 0.5  # raise to ignore short noise bursts

# Already tuned for dry-run, may need adjustment for AIOC:
aioc:
  serial_port: auto     # or explicit: /dev/cu.usbmodem14301
  audio_device: "AllInOneCable"
```
