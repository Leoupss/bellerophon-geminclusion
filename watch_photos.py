#!/usr/bin/env python3
"""
watch_photos.py
Watches  <repo>/Deposer Photo  and auto-generates Hugo inclusion pages.
Drop a photo → index.md + photo copy created in content/inclusions/<slug>/.
Photo is then deleted from the watch folder.
Polls every 5 seconds.
"""

import io
import re
import shutil
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

# ── UTF-8 output on Windows terminals ──────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── PATHS ──────────────────────────────────────────────────────────────────────
REPO_DIR    = Path(__file__).parent.resolve()
WATCH_DIR   = REPO_DIR / "Deposer Photo"
CONTENT_DIR = REPO_DIR / "content" / "inclusions"
POLL_SECS   = 5
PHOTO_EXTS  = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# ── GEMOLOGICAL DICTIONARIES ───────────────────────────────────────────────────
# Longest-first matching: always put longer aliases before shorter ones.

HOST_STONES = {
    "alexandrite": "Alexandrite",
    "aquamarine":  "Aquamarine",
    "chrysoberyl": "Chrysoberyl",
    "tourmaline":  "Tourmaline",
    "tsavorite":   "Tsavorite",
    "demantoid":   "Demantoid",
    "tanzanite":   "Tanzanite",
    "sapphire":    "Corundum — Sapphire",
    "peridot":     "Peridot",
    "paraiba":     "Paraíba Tourmaline",
    "emerald":     "Emerald",
    "diamond":     "Diamond",
    "garnet":      "Garnet",
    "spinel":      "Spinel",
    "topaz":       "Topaz",
    "zircon":      "Zircon",
    "ruby":        "Corundum — Ruby",
    "opal":        "Opal",
}

ORIGINS = {
    "afghanistan": "Afghanistan",
    "madagascar":  "Madagascar",
    "mozambique":  "Mozambique",
    "tajikistan":  "Tajikistan",
    "australian":  "Australia",
    "australia":   "Australia",
    "colombian":   "Colombia",
    "colombia":    "Colombia",
    "sri lanka":   "Sri Lanka",
    "thailand":    "Thailand",
    "tanzania":    "Tanzania",
    "pakistan":    "Pakistan",
    "cambodia":    "Cambodia",
    "myanmar":     "Myanmar",
    "vietnam":     "Vietnam",
    "nigeria":     "Nigeria",
    "kashmir":     "Kashmir",
    "russian":     "Russia",
    "ceylon":      "Sri Lanka (Ceylon)",
    "chinese":     "China",
    "brazil":      "Brazil",
    "russia":      "Russia",
    "china":       "China",
    "kenya":       "Kenya",
    "burma":       "Burma",
    "tajik":       "Tajikistan",
    "siam":        "Thailand (Siam)",
    "thai":        "Thailand",
    "mada":        "Madagascar",
}

# Multi-word treatments matched before single-word ones
TREATMENTS = {
    "fracture filled": "Fracture Filled",
    "no treatment":    "No Treatment",
    "heat treated":    "Heat Treated",
    "glass filled":    "Glass Filling",
    "lead glass":      "Lead Glass Filling",
    "beryllium":       "Beryllium Diffusion",
    "irradiated":      "Irradiated",
    "unheated":        "Unheated",
    "diffusion":       "Diffusion",
    "coated":          "Coated",
    "heated":          "Heated",
    "filled":          "Filled",
    "oiled":           "Oiled",
    "heat":            "Heated",
}

# Diagnostic notes for known (host_key, inclusion_key) pairs
DIAGNOSTICS: dict[tuple, str] = {
    ("sapphire", "silk"):        "Intact rutile silk dissolves above 1,200 °C — a key indicator of no heat treatment.",
    ("ruby",     "silk"):        "Fine, regular silk confirms the absence of heat treatment in this ruby.",
    ("sapphire", "rutile"):      "Oriented rutile crystals attest to slow crystallisation in a metamorphic or magmatic environment.",
    ("sapphire", "fingerprint"): "Fingerprints are partially healed fractures, typical of natural, unheated corundum.",
    ("ruby",     "fingerprint"): "Fingerprints indicate a fracture healing during crystal growth.",
    ("sapphire", "apatite"):     "Apatite indicates a calc-silicate metamorphic environment, common in Madagascar and Sri Lanka sapphires.",
    ("ruby",     "apatite"):     "Apatite associated with ruby is often characteristic of a marble-hosted deposit.",
    ("spinel",   "apatite"):     "Apatite in spinel is typical of high-pressure metamorphic deposits (Tajikistan, Myanmar).",
    ("spinel",   "calcite"):     "Calcite confirms a carbonate metamorphic formation environment, common in Tajikistan spinels.",
    ("sapphire", "calcite"):     "Calcite confirms a calc-silicate metamorphic context, typical of Madagascar sapphires.",
    ("emerald",  "three-phase"): "Three-phase inclusions (solid + liquid + gas) are a distinctive marker of Colombian emeralds.",
    ("emerald",  "two-phase"):   "Two-phase inclusions are common in hydrothermally-formed emeralds.",
}
DIAG_DEFAULT = "Document the diagnostic interest of this inclusion."

# ── HELPERS ────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def find_match(text: str, dictionary: dict) -> tuple[str | None, str | None]:
    """Return (key, value) for the longest key found as a whole word in text."""
    for key in sorted(dictionary, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", text):
            return key, dictionary[key]
    return None, None


def remove_token(text: str, token: str) -> str:
    text = re.sub(r"(?<![a-z])" + re.escape(token) + r"(?![a-z])", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_stem(path: Path) -> str:
    """Strip all known photo extensions (handles double-extension like .jpg.jpg)."""
    name = path.name
    for _ in range(3):
        p = Path(name)
        if p.suffix.lower() in PHOTO_EXTS:
            name = p.stem
        else:
            break
    return name


def photo_dest_name(src_path: Path) -> str:
    """Normalize destination filename: jpeg variants → photo.jpg, rest kept."""
    ext = Path(src_path.name.lower())
    while ext.suffix in PHOTO_EXTS:
        actual_ext = ext.suffix
        ext = Path(ext.stem)
    if actual_ext in {".jpg", ".jpeg"}:
        return "photo.jpg"
    return f"photo{actual_ext}"


def unique_folder(base_slug: str) -> Path:
    """Return a content/inclusions/<slug> Path that doesn't exist yet."""
    slug, n = base_slug, 2
    while (CONTENT_DIR / slug).exists():
        slug = f"{base_slug}-{n}"
        n += 1
    return CONTENT_DIR / slug

# ── PARSING ────────────────────────────────────────────────────────────────────

def parse_filename(path: Path) -> dict:
    stem = clean_stem(path)

    # 1. Magnification  (x50, X150, ×300, x 200 …)
    mag_match = re.search(r"[xX×]\s*(\d+)", stem)
    magnification = f"×{mag_match.group(1)}" if mag_match else ""
    work = re.sub(r"-?\s*[xX×]\s*\d+", " ", stem)

    # Remove stray numbers
    work = re.sub(r"(?<![a-zA-Z])\d+(?:-\d+)?(?![a-zA-Z])", " ", work)
    work = re.sub(r"[-_]+", " ", work)
    work = re.sub(r"\s+", " ", work).strip()
    text = work.lower()

    # 2. Host stone
    host_key, host_val = find_match(text, HOST_STONES)
    if host_key:
        text = remove_token(text, host_key)

    # 3. Origin
    origin_key, origin_val = find_match(text, ORIGINS)
    if origin_key:
        text = remove_token(text, origin_key)

    # 4. Treatment
    treat_key, treat_val = find_match(text, TREATMENTS)
    if treat_key:
        text = remove_token(text, treat_key)

    # 5. Remaining text = inclusion type
    inclusion_raw = re.sub(r"\s+", " ", text).strip()
    inclusion = inclusion_raw.title() if inclusion_raw else ""

    # 6. Diagnostic note
    diag_key = (host_key or "", inclusion_raw)
    diagnostic = DIAGNOSTICS.get(diag_key, DIAG_DEFAULT)

    return {
        "host":        host_val  or "Unidentified",
        "host_key":    host_key  or "",
        "origin":      origin_val or "Not identified",
        "treatment":   treat_val  or "None detected",
        "inclusion":   inclusion,
        "inclusion_raw": inclusion_raw,
        "magnification": magnification,
        "diagnostic":  diagnostic,
    }


def build_title(data: dict) -> str:
    inc    = data["inclusion"] or "Inclusion"
    host   = data["host"]
    origin = data["origin"]
    treat  = data["treatment"]

    title = inc
    if host not in ("", "Unidentified"):
        neutral = {"None detected", "Unheated", "No Treatment"}
        title += f" in {host}"
        if treat and treat not in neutral:
            title += f" ({treat.lower()})"
    if origin not in ("", "Not identified"):
        title += f" — {origin}"
    return title


def build_frontmatter(data: dict, title: str) -> str:
    today = date.today().isoformat()
    lines = [
        "---",
        f'title: "{title}"',
        f"date: {today}",
        "draft: false",
        f'pierre_hote: "{data["host"]}"',
        f'type_inclusion: "{data["inclusion"]}"',
        f'origine: "{data["origin"]}"',
        f'traitement: "{data["treatment"]}"',
    ]
    if data["magnification"]:
        lines.append(f'grossissement: "{data["magnification"]}"')
    lines.append(f'interet_diagnostique: "{data["diagnostic"]}"')
    lines.append("---")
    return "\n".join(lines) + "\n"

# ── PROCESSING ─────────────────────────────────────────────────────────────────

def ensure_index_md():
    """Create content/inclusions/_index.md if missing."""
    idx = CONTENT_DIR / "_index.md"
    if not idx.exists():
        CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        idx.write_text(
            '---\ntitle: "Inclusion database"\n'
            'description: "Complete catalogue of documented gemological inclusions'
            ' — filterable by host stone, origin and treatment"\n---\n',
            encoding="utf-8",
        )


def process_photo(photo: Path) -> bool:
    """Parse photo, create Hugo page, delete source. Returns True on success."""
    data  = parse_filename(photo)

    # Build slug from inclusion + host + origin
    slug_parts = [data["inclusion_raw"], data["host_key"], data["origin"].lower()]
    base_slug  = slugify(" ".join(p for p in slug_parts if p)) or slugify(photo.stem)
    folder     = unique_folder(base_slug)
    folder.mkdir(parents=True, exist_ok=True)

    title   = build_title(data)
    content = build_frontmatter(data, title)

    # Write index.md — UTF-8, no BOM
    index_path = folder / "index.md"
    index_path.write_text(content, encoding="utf-8")

    # Copy photo
    dest_name = photo_dest_name(photo)
    shutil.copy2(photo, folder / dest_name)

    # Delete source
    photo.unlink()

    # Terminal report
    w = 18
    slug_rel = folder.relative_to(REPO_DIR)
    print(f"\n{'─'*60}")
    print(f"  Photo      : {photo.name}")
    print(f"  {'Host stone':<{w}}: {data['host']}")
    print(f"  {'Inclusion':<{w}}: {data['inclusion'] or '—'}")
    print(f"  {'Origin':<{w}}: {data['origin']}")
    print(f"  {'Treatment':<{w}}: {data['treatment']}")
    print(f"  {'Magnification':<{w}}: {data['magnification'] or '—'}")
    print(f"  {'Title':<{w}}: {title}")
    print(f"  ✓ Created   : {slug_rel}/index.md")
    print(f"  ✓ Photo     : {slug_rel}/{dest_name}")
    return True

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────

def main():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_index_md()

    print("=" * 60)
    print("  watch_photos.py — Bellerophon Includia")
    print("=" * 60)
    print(f"  Watching : {WATCH_DIR}")
    print(f"  Output   : {CONTENT_DIR}")
    print(f"  Polling  : every {POLL_SECS}s   (Ctrl+C to stop)")
    print("=" * 60)

    while True:
        photos = sorted(
            p for p in WATCH_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in PHOTO_EXTS
        )
        for photo in photos:
            try:
                process_photo(photo)
            except Exception as exc:
                print(f"\n  [ERROR] {photo.name}: {exc}")
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped.")
