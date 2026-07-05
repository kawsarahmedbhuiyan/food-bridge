# FoodBridge Presentation Assets

Materials for **FoodBridge-CREATE-a-Thon-Deck.pptx**.

| File | Description |
|------|-------------|
| `FoodBridge-Speaker-Script.md` | Full narration script with timing, slide cues, and Q&A prep |
| `FoodBridge-Presentation.mp4` | Auto-generated narrated video (~7 min) |
| `slides/slide-NN.png` | Visual slide cards (1920×1080) |
| `audio/slide-NN.aiff` | macOS TTS narration per slide |

## Regenerate

```bash
pip install Pillow imageio-ffmpeg
python scripts/build_presentation_video.py
```

## Record with the official deck

1. Open `FoodBridge-CREATE-a-Thon-Deck.pptx` in PowerPoint.
2. Use `FoodBridge-Speaker-Script.md` as your teleprompter.
3. Record via **Slide Show → Record** or OBS while playing `audio/slide-NN.aiff` in sync.

## Prefer the official slides in video?

Replace `presentation/slides/*.png` with exports from PowerPoint, then re-run with existing audio:

```bash
python scripts/build_presentation_video.py --skip-audio
```
