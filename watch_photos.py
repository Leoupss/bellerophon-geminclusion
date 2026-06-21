#!/usr/bin/env python3
"""
watch_photos.py — Surveille "Deposer Photo/" et génère les fiches inclusions Hugo.

Formats acceptés (espaces ou underscores) :
  Ruby Mozambique - rosette x50 (2).jpg
  Ruby_Mozambique_-_rosette_x50_(2).jpg
"""

import re
import shutil
import sys
import time
from pathlib import Path

# Force UTF-8 output so ✓ and em dashes display correctly on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT       = Path(__file__).parent
INBOX      = ROOT / "Deposer Photo"
INCLUSIONS = ROOT / "content" / "inclusions"

IMAGE_EXT  = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
TREATMENTS = {"heated", "unheated", "filled", "beryllium"}


def parse_filename(stem: str) -> dict | None:
    # 1. Supprimer le numéro final : " (2)", "_(2)", "(2)"
    folder_name = re.sub(r"[\s_]*\(\d+\)\s*$", "", stem).strip()

    # 2. Normaliser pour le parsing : underscores → espaces, "_-_" → " - "
    normalized = folder_name.replace("_-_", " - ").replace("_", " ")

    # 3. Séparer sur " - "
    if " - " not in normalized:
        return None
    left, right = normalized.split(" - ", 1)
    left  = left.strip()
    right = right.strip()

    # 4. Partie gauche : dernier mot = origine, le reste = pierre
    parts   = left.split()
    pierre  = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
    origine = parts[-1]

    # 5. Partie droite : grossissement (x+chiffres), traitement, inclusion
    grossissement   = ""
    treatments      = []
    inclusion_parts = []

    for p in right.split():
        if re.fullmatch(r"x\d+", p, re.IGNORECASE):
            grossissement = "x" + re.fullmatch(r"x(\d+)", p, re.IGNORECASE).group(1)
        elif p.lower() in TREATMENTS:
            treatments.append(p.capitalize())
        else:
            inclusion_parts.append(p)

    inclusion  = " ".join(inclusion_parts) if inclusion_parts else "Not specified"
    traitement = ", ".join(treatments) if treatments else "None detected"

    return {
        "folder_name":    folder_name,
        "title":          f"{inclusion} in {pierre} — {origine}",
        "pierre_hote":    pierre,
        "type_inclusion": inclusion,
        "origine":        origine,
        "traitement":     traitement,
        "grossissement":  grossissement,
    }


def write_index(target_dir: Path, d: dict) -> None:
    content = (
        "---\n"
        f'title: "{d["title"]}"\n'
        f'pierre_hote: "{d["pierre_hote"]}"\n'
        f'type_inclusion: "{d["type_inclusion"]}"\n'
        f'origine: "{d["origine"]}"\n'
        f'traitement: "{d["traitement"]}"\n'
        f'grossissement: "{d["grossissement"]}"\n'
        "draft: false\n"
        "---\n"
    )
    (target_dir / "index.md").write_text(content, encoding="utf-8")


def process(photo: Path) -> None:
    d = parse_filename(photo.stem)
    if d is None:
        print(f"⚠  Format non reconnu : {photo.name}")
        return

    target = INCLUSIONS / d["folder_name"]
    target.mkdir(parents=True, exist_ok=True)

    shutil.copy2(photo, target / "photo.jpg")
    write_index(target, d)
    photo.unlink()

    print(f"✓ Créé : {d['folder_name']}")


def watch() -> None:
    INBOX.mkdir(exist_ok=True)
    INCLUSIONS.mkdir(parents=True, exist_ok=True)

    print(f"Surveillance de : {INBOX}")
    print("Ctrl+C pour arrêter.\n")

    while True:
        try:
            for photo in sorted(INBOX.iterdir()):
                if photo.is_file() and photo.suffix.lower() in IMAGE_EXT:
                    time.sleep(0.3)
                    if photo.exists():
                        try:
                            process(photo)
                        except Exception as e:
                            print(f"✗ Erreur ({photo.name}) : {e}")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt.")
            break


if __name__ == "__main__":
    watch()
