#!/usr/bin/env python3
"""
Build narrated presentation assets for FoodBridge-CREATE-a-Thon-Deck.pptx.

Outputs:
  presentation/audio/slide-NN.aiff   — macOS TTS narration per slide
  presentation/slides/slide-NN.png   — visual cards for video assembly
  presentation/FoodBridge-Presentation.mp4 — if ffmpeg is available

Usage:
  python scripts/build_presentation_video.py
  python scripts/build_presentation_video.py --video-only   # skip say, use existing audio
"""

from typing import Optional

import argparse
import shutil
import subprocess
import textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Install Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "presentation"
AUDIO_DIR = OUT_DIR / "audio"
SLIDES_DIR = OUT_DIR / "slides"
VIDEO_OUT = OUT_DIR / "FoodBridge-Presentation.mp4"

W, H = 1920, 1080
BG = (15, 20, 25)
TEAL = (15, 92, 92)
ACCENT = (45, 138, 110)
TEXT = (232, 238, 244)
MUTED = (139, 163, 188)

# Narration aligned with FoodBridge-Speaker-Script.md (condensed for TTS)
NARRATIONS = [
    (
        "Slide 1 — FoodBridge",
        "Good afternoon. We're presenting FoodBridge, an agentic A I system for food waste redistribution. "
        "FoodBridge connects surplus food to communities in need, safely, fairly, and transparently. "
        "This is our CREATE-a-Thon proof of concept for Toronto.",
    ),
    (
        "Slide 2 — The Problem",
        "Food waste and hunger coexist in the same city. Restaurants discard edible surplus while shelters "
        "lack reliable supply. Four groups are impacted: donors, community kitchens, volunteer drivers, "
        "and cities. Today surplus food never reliably reaches hungry communities. FoodBridge replaces "
        "that gap with specialized A I agents using real Dinesafe, Biomass, and food-security data.",
    ),
    (
        "Slide 3 — Ethics",
        "Ethics are built in from the start. Safety: Dinesafe Pass-only donors, crucial infractions excluded. "
        "Fairness: small organizations prioritized. Transparency: every agent decision is logged. "
        "Privacy: aggregate data only. Accountability: a human must approve before any pickup. "
        "Matching uses auditable rules, not a black box.",
    ),
    (
        "Slide 4 — Architecture",
        "Six specialized agents use four datasets. Dinesafe for safe donors. Biomass for waste hotspots. "
        "G D E L T for hunger signals. Supply chain for disruption context. "
        "Agents run in sequence: Surplus Estimator, Need Prioritizer, Donor Scout, Matcher, "
        "Logistics Planner, and Ethics Guardian. Data flows in, matches and routes flow out, "
        "with human sign-off at the end.",
    ),
    (
        "Slide 5 — Demo",
        "FoodBridge runs as a command-line tool and a web dashboard. Run python main dot py with a region "
        "to print matches, routes, and ethics reports. The web app shows an interactive map, agent pipeline, "
        "match cards, and an ethics panel. Every match shows distance, Dinesafe status, and approval state.",
    ),
    (
        "Slide 6 — Scalability",
        "Today we have a Toronto proof of concept. Next, a pilot with partner kitchens and donor alerts. "
        "At scale, multi-city data adapters and an API for N G Os and grocers. "
        "Agents are modular, so the same pipeline works in any city by swapping datasets. "
        "This supports municipal food security and waste diversion programs.",
    ),
    (
        "Slide 7 — Closing",
        "Biomass finds waste hotspots. G D E L T finds hunger hotspots. Dinesafe finds safe donors. "
        "Our agents build a fair pickup plan. Thank you. We welcome your questions.",
    ),
]

SLIDE_VISUALS = [
    ("FoodBridge", "Agentic AI for Food Waste Redistribution\nCREATE-a-Thon · Toronto\n\nConnecting surplus food to communities in need\n— safely, fairly, and transparently —"),
    ("The Problem", "Food waste and hunger coexist in the same city\n\n• Donors discard edible surplus\n• Kitchens lack reliable supply\n• No coordinator links safety + logistics\n\nSurplus → ? → Communities\nFoodBridge replaces the ?"),
    ("Ethical Considerations", "Safety · Pass-only Dinesafe donors\nFairness · Small orgs prioritized\nTransparency · Step-level audit trail\nPrivacy · Aggregate data only\nAccountability · Human approval required\nBias · Rule-based auditable matching"),
    ("Proof of Concept", "6 Agents · 4 Datasets\n\nSurplus Estimator → Need Prioritizer → Donor Scout\n→ Matcher → Logistics Planner → Ethics Guardian\n\nDinesafe · Biomass · GDELT · Supply chain"),
    ("Live Demo", "CLI: python main.py --region Scarborough --top 3\n\nWeb: uvicorn web.app:app --port 8000\n\nMap · Agent pipeline · Matches · Route · Ethics"),
    ("Scalability", "POC → Pilot → City-wide\n\nToronto datasets today\nPartner kitchens + SMS alerts next\nMulti-city API at scale"),
    ("Thank You", "Biomass → waste hotspots\nGDELT → hunger hotspots\nDinesafe → safe donors\nAgents → fair pickup plan\n\nQuestions?"),
]


def _font(size: int, bold: bool = False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render_slide(idx: int, title: str, body: str) -> Path:
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 8], fill=ACCENT)
    draw.rectangle([0, H - 6, W, H], fill=TEAL)

    title_font = _font(72, bold=True)
    body_font = _font(36)
    small_font = _font(28)

    draw.text((80, 80), title, fill=ACCENT, font=title_font)
    y = 200
    for line in body.split("\n"):
        if line.strip():
            draw.text((80, y), line.strip(), fill=TEXT if not line.startswith("•") else MUTED, font=body_font)
        y += 52

    draw.text((80, H - 60), f"FoodBridge · Slide {idx + 1} of {len(SLIDE_VISUALS)}", fill=MUTED, font=small_font)
    path = SLIDES_DIR / f"slide-{idx + 1:02d}.png"
    img.save(path)
    return path


def synthesize_audio(idx: int, text: str) -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    aiff = AUDIO_DIR / f"slide-{idx + 1:02d}.aiff"
    subprocess.run(["say", "-o", str(aiff), text], check=True)
    return aiff


def _find_ffmpeg() -> Optional[str]:
    for name in ("ffmpeg",):
        p = shutil.which(name)
        if p:
            return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def build_video(slide_paths: list[Path], audio_paths: list[Path]) -> bool:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        print("ffmpeg not found — skipping MP4. Install ffmpeg or: pip install imageio-ffmpeg")
        return False

    list_file = OUT_DIR / "concat_list.txt"
    segments: list[Path] = []

    for i, (sp, ap) in enumerate(zip(slide_paths, audio_paths)):
        seg = OUT_DIR / f"segment_{i + 1:02d}.mp4"
        # Get audio duration
        probe = subprocess.run(
            [ffmpeg, "-i", str(ap), "-f", "null", "-"],
            capture_output=True,
            text=True,
        )
        # Default 8s if probe fails
        duration = 8.0
        for line in (probe.stderr or "").split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                duration = float(h) * 3600 + float(m) * 60 + float(s)
                break
        duration = max(duration + 0.5, 5.0)

        vf = (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        subprocess.run(
            [
                ffmpeg, "-y",
                "-loop", "1", "-i", str(sp),
                "-i", str(ap),
                "-vf", vf,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                str(seg),
            ],
            check=True,
            capture_output=True,
        )
        segments.append(seg)

    with list_file.open("w") as f:
        for seg in segments:
            f.write(f"file '{seg.resolve()}'\n")

    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(VIDEO_OUT)],
        check=True,
        capture_output=True,
    )
    for seg in segments:
        seg.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-audio", action="store_true", help="Reuse existing presentation/audio/*.aiff")
    parser.add_argument("--skip-render", action="store_true", help="Reuse existing presentation/slides/slide-NN.png")
    parser.add_argument("--skip-video", action="store_true")
    args = parser.parse_args()

    slide_paths: list[Path] = []
    audio_paths: list[Path] = []

    for i in range(len(NARRATIONS)):
        if args.skip_render:
            sp = SLIDES_DIR / f"slide-{i + 1:02d}.png"
            if not sp.exists():
                raise SystemExit(f"Missing slide image: {sp}")
            slide_paths.append(sp)
            print(f"Using {sp.name}")
        else:
            (title, narration), (vtitle, vbody) = NARRATIONS[i], SLIDE_VISUALS[i]
            sp = render_slide(i, vtitle, vbody)
            slide_paths.append(sp)
            print(f"Rendered {sp.name}")

        if args.skip_audio:
            ap = AUDIO_DIR / f"slide-{i + 1:02d}.aiff"
            if not ap.exists():
                raise SystemExit(f"Missing audio: {ap}")
            audio_paths.append(ap)
        else:
            _, narration = NARRATIONS[i]
            ap = synthesize_audio(i, narration)
            audio_paths.append(ap)
            print(f"Narrated {ap.name}")

    if not args.skip_video and audio_paths:
        if build_video(slide_paths, audio_paths):
            print(f"\nVideo saved: {VIDEO_OUT}")
        else:
            print(f"\nAssets ready in {OUT_DIR}/")
            print("Record manually: open deck + play audio/slides, or install ffmpeg and re-run.")
    elif args.skip_video:
        print(f"\nSlides and script ready in {OUT_DIR}/")

    print(f"Speaker script: {OUT_DIR / 'FoodBridge-Speaker-Script.md'}")


if __name__ == "__main__":
    main()
