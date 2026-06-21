#!/usr/bin/env python3
"""
auto_inclusions.py
Scans a folder of gemological photomicrographs, parses filenames with
gemological dictionaries, and generates Hugo content pages (FR + EN).
"""

import io
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from datetime import date

# Force UTF-8 output on Windows terminals that default to cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
PHOTO_DIR    = Path(r"C:\Users\movix\Desktop\Photo\photo Theo test")
REPO_DIR     = Path(r"C:\Users\movix\Documents\bellerophon-geminclusion")
# True  → creates content/fr/inclusions/[slug]  AND  content/en/inclusions/[slug]
# False → creates content/inclusions/[slug]  (monolingual English structure)
MULTILINGUAL = False
TODAY        = date.today().isoformat()
PHOTO_EXTS   = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# ─── GEMOLOGICAL DICTIONARIES ──────────────────────────────────────────────────
# Format: lowercase English key → {"fr": French label, "en": English label}

HOST_STONES = {
    "ruby":        {"fr": "Corindon — Rubis",    "en": "Corundum — Ruby"},
    "sapphire":    {"fr": "Corindon — Saphir",   "en": "Corundum — Sapphire"},
    "spinel":      {"fr": "Spinelle",             "en": "Spinel"},
    "emerald":     {"fr": "Émeraude",             "en": "Emerald"},
    "alexandrite": {"fr": "Alexandrite",          "en": "Alexandrite"},
    "tourmaline":  {"fr": "Tourmaline",           "en": "Tourmaline"},
    "garnet":      {"fr": "Grenat",               "en": "Garnet"},
    "diamond":     {"fr": "Diamant",              "en": "Diamond"},
    "aquamarine":  {"fr": "Aigue-marine",         "en": "Aquamarine"},
    "tanzanite":   {"fr": "Tanzanite",            "en": "Tanzanite"},
    "paraiba":     {"fr": "Tourmaline Paraíba",   "en": "Paraíba Tourmaline"},
    "tsavorite":   {"fr": "Tsavorite",            "en": "Tsavorite"},
    "demantoid":   {"fr": "Démantoïde",           "en": "Demantoid"},
    "chrysoberyl": {"fr": "Chrysobéryl",          "en": "Chrysoberyl"},
    "topaz":       {"fr": "Topaze",               "en": "Topaz"},
    "peridot":     {"fr": "Péridot",              "en": "Peridot"},
    "opal":        {"fr": "Opale",                "en": "Opal"},
    "zircon":      {"fr": "Zircon",               "en": "Zircon"},
}

ORIGINS = {
    "sri lanka":   {"fr": "Sri Lanka",            "en": "Sri Lanka"},
    "madagascar":  {"fr": "Madagascar",           "en": "Madagascar"},
    "tajikistan":  {"fr": "Tadjikistan",          "en": "Tajikistan"},
    "mozambique":  {"fr": "Mozambique",           "en": "Mozambique"},
    "australia":   {"fr": "Australie",            "en": "Australia"},
    "colombia":    {"fr": "Colombie",             "en": "Colombia"},
    "kashmir":     {"fr": "Cachemire",            "en": "Kashmir"},
    "tanzania":    {"fr": "Tanzanie",             "en": "Tanzania"},
    "pakistan":    {"fr": "Pakistan",             "en": "Pakistan"},
    "vietnam":     {"fr": "Viêt Nam",             "en": "Vietnam"},
    "cambodia":    {"fr": "Cambodge",             "en": "Cambodia"},
    "nigeria":     {"fr": "Nigéria",              "en": "Nigeria"},
    "myanmar":     {"fr": "Myanmar",              "en": "Myanmar"},
    "russia":      {"fr": "Russie",               "en": "Russia"},
    "brazil":      {"fr": "Brésil",               "en": "Brazil"},
    "china":       {"fr": "Chine",                "en": "China"},
    "afghanistan": {"fr": "Afghanistan",          "en": "Afghanistan"},
    "kenya":       {"fr": "Kenya",                "en": "Kenya"},
    # Aliases (shorter — must come after longer keys when sorted by length)
    "australian":  {"fr": "Australie",            "en": "Australia"},
    "colombian":   {"fr": "Colombie",             "en": "Colombia"},
    "thailand":    {"fr": "Thaïlande",            "en": "Thailand"},
    "ceylon":      {"fr": "Sri Lanka (Ceylan)",   "en": "Sri Lanka (Ceylon)"},
    "russian":     {"fr": "Russie",               "en": "Russia"},
    "chinese":     {"fr": "Chine",                "en": "China"},
    "burma":       {"fr": "Birmanie",             "en": "Burma"},
    "brazil":      {"fr": "Brésil",               "en": "Brazil"},
    "siam":        {"fr": "Thaïlande (Siam)",     "en": "Thailand (Siam)"},
    "mada":        {"fr": "Madagascar",           "en": "Madagascar"},
    "thai":        {"fr": "Thaïlande",            "en": "Thailand"},
    "tajik":       {"fr": "Tadjikistan",          "en": "Tajikistan"},
}

# Sorted longest-first to ensure "fracture filled" beats "filled", etc.
TREATMENTS = {
    "fracture filled": {"fr": "Remplissage de fractures", "en": "Fracture Filled"},
    "heat treated":    {"fr": "Traitement thermique",     "en": "Heat Treated"},
    "glass filled":    {"fr": "Remplissage verre",        "en": "Glass Filling"},
    "lead glass":      {"fr": "Remplissage verre-plomb",  "en": "Lead Glass Filling"},
    "beryllium":       {"fr": "Diffusion béryllium",      "en": "Beryllium Diffusion"},
    "diffusion":       {"fr": "Diffusion",                "en": "Diffusion"},
    "unheated":        {"fr": "Non chauffé",              "en": "Unheated"},
    "irradiated":      {"fr": "Irradié",                  "en": "Irradiated"},
    "coated":          {"fr": "Revêtement",               "en": "Coated"},
    "heated":          {"fr": "Chauffé",                  "en": "Heated"},
    "filled":          {"fr": "Remplissage",              "en": "Filled"},
    "oiled":           {"fr": "Huilé",                    "en": "Oiled"},
}

# English inclusion term → French translation (longest key matched first)
INCLUSION_FR = {
    "fish eyes":        "Yeux de poisson",
    "fish eye":         "Œil de poisson",
    "growth tube":      "Tube de croissance",
    "negative crystal": "Cristal négatif",
    "two-phase":        "Triphasé",
    "three-phase":      "Triphasé",
    "fingerprint":      "Empreinte digitale",
    "hornblende":       "Hornblende",
    "phlogopite":       "Phlogopite",
    "pyrrhotite":       "Pyrrhotite",
    "ilmenite":         "Ilménite",
    "chromite":         "Chromite",
    "boehmite":         "Böhmite",
    "amphibole":        "Amphibole",
    "tourmaline":       "Tourmaline",
    "platelets":        "Plaquettes",
    "platelet":         "Plaquette",
    "needles":          "Aiguilles",
    "rosettes":         "Rosettes",
    "apatite":          "Apatite",
    "calcite":          "Calcite",
    "diaspore":         "Diaspore",
    "graphite":         "Graphite",
    "olivine":          "Olivine",
    "pyrite":           "Pyrite",
    "garnet":           "Grenat",
    "spinel":           "Spinelle",
    "rutile":           "Rutile",
    "feather":          "Plume",
    "needle":           "Aiguille",
    "rosette":          "Rosette",
    "zircon":           "Zircon",
    "cobalt":           "Cobalt",
    "crystal":          "Cristal",
    "healing":          "Cicatrice de fracture",
    "cleavage":         "Clivage",
    "fracture":         "Fracture",
    "liquid":           "Liquide",
    "cloud":            "Nuage",
    "veil":             "Voile",
    "cavity":           "Cavité",
    "halo":             "Halo",
    "tube":             "Tube",
    "silk":             "Soie",
    "mica":             "Mica",
}

# Bilingual diagnostic notes for known (host_key, inclusion_key) pairs
DIAGNOSTICS: dict[tuple, dict] = {
    ("sapphire", "silk"): {
        "fr": "La soie de rutile intacte se dissout au-dessus de 1 200 °C — marqueur clé de l'absence de chauffage.",
        "en": "Intact rutile silk dissolves above 1,200 °C — a key indicator of no heat treatment.",
    },
    ("ruby", "silk"): {
        "fr": "La soie fine et régulière confirme l'absence de traitement thermique sur ce rubis.",
        "en": "Fine, regular silk confirms the absence of heat treatment in this ruby.",
    },
    ("sapphire", "rutile"): {
        "fr": "Les cristaux de rutile orientés attestent d'une cristallisation lente en milieu métamorphique ou magmatique.",
        "en": "Oriented rutile crystals attest to slow crystallisation in a metamorphic or magmatic environment.",
    },
    ("sapphire", "fingerprint"): {
        "fr": "Les empreintes digitales sont des fractures partiellement guéries, typiques des corindons naturels et non chauffés.",
        "en": "Fingerprints are partially healed fractures, typical of natural, unheated corundum.",
    },
    ("ruby", "fingerprint"): {
        "fr": "Les empreintes digitales indiquent une fracture en voie de guérison lors de la croissance du cristal.",
        "en": "Fingerprints indicate a fracture healing during crystal growth.",
    },
    ("sapphire", "apatite"): {
        "fr": "L'apatite est indicatrice d'un milieu métamorphique calc-silicaté, fréquent à Madagascar et au Sri Lanka.",
        "en": "Apatite indicates a calc-silicate metamorphic environment, common in Madagascar and Sri Lanka sapphires.",
    },
    ("ruby", "apatite"): {
        "fr": "L'apatite associée au rubis est souvent caractéristique d'un gisement en contexte marbré.",
        "en": "Apatite associated with ruby is often characteristic of a marble-hosted deposit.",
    },
    ("spinel", "apatite"): {
        "fr": "L'apatite dans le spinelle est typique des gisements métamorphiques de haute pression (Tadjikistan, Myanmar).",
        "en": "Apatite in spinel is typical of high-pressure metamorphic deposits (Tajikistan, Myanmar).",
    },
    ("spinel", "calcite"): {
        "fr": "La calcite confirme un environnement de formation métamorphique carbonaté, fréquent pour les spinelles de Tadjikistan.",
        "en": "Calcite confirms a carbonate metamorphic formation environment, common in Tajikistan spinels.",
    },
    ("sapphire", "calcite"): {
        "fr": "La calcite confirme un contexte métamorphique calc-silicaté, typique des saphirs de Madagascar.",
        "en": "Calcite confirms a calc-silicate metamorphic context, typical of Madagascar sapphires.",
    },
    ("emerald", "three-phase"): {
        "fr": "Les inclusions triphasées (solide + liquide + gaz) sont un marqueur distinctif des émeraudes de Colombie.",
        "en": "Three-phase inclusions (solid + liquid + gas) are a distinctive marker of Colombian emeralds.",
    },
    ("emerald", "two-phase"): {
        "fr": "Les inclusions biphasées sont courantes dans les émeraudes d'origine hydrothermale.",
        "en": "Two-phase inclusions are common in hydrothermally-formed emeralds.",
    },
}

DIAG_DEFAULT = {
    "fr": "Documenter l'intérêt diagnostique de cette inclusion.",
    "en": "Document the diagnostic interest of this inclusion.",
}

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def find_in_dict(text: str, dictionary: dict) -> tuple:
    """Return (key, value) for the first (longest) key found as a whole word."""
    for key in sorted(dictionary, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", text):
            return key, dictionary[key]
    return None, None


def real_suffix(path: Path) -> str:
    """Return actual extension, handling double extensions like .jpg.jpg."""
    name = path.name.lower()
    for ext in PHOTO_EXTS:
        double = ext + ext  # e.g. .jpg.jpg → no, handle differently
        if name.endswith(ext[1:] + ext):  # e.g. name ends in "jpgjpg" — unlikely
            return ext
    # Handle .jpg.jpg specifically
    for ext in PHOTO_EXTS:
        if name.endswith(ext + ext[1:] + ext[1:]):  # not matching well
            pass
    # Simplest: check if stripping suffix once still has a known ext
    stem = path.stem
    if Path(stem).suffix.lower() in PHOTO_EXTS:
        return Path(stem).suffix.lower()
    return path.suffix.lower()


def clean_stem(path: Path) -> str:
    """Extract the base name, stripping all known extensions (handles .jpg.jpg)."""
    name = path.name
    for _ in range(3):
        p = Path(name)
        if p.suffix.lower() in PHOTO_EXTS:
            name = p.stem
        else:
            break
    return name


def translate_inclusion(en_text: str) -> str:
    """Translate English inclusion terms to French (longest match first)."""
    text = en_text.lower().strip()
    if not text:
        return "Non identifié"
    for key in sorted(INCLUSION_FR, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", text):
            text = re.sub(
                r"(?<![a-z])" + re.escape(key) + r"(?![a-z])",
                INCLUSION_FR[key],
                text,
                count=1,
            )
    return text.strip().capitalize()


# ─── PARSING ───────────────────────────────────────────────────────────────────

def parse_photo(path: Path) -> dict:
    stem = clean_stem(path)

    # 1. Extract magnification (e.g. x150, X300, ×200)
    mag_match = re.search(r"[xX×]\s*(\d+)", stem)
    magnification = f"×{mag_match.group(1)}" if mag_match else ""

    # Remove magnification token (including optional leading hyphen)
    work = re.sub(r"-?\s*[xX×]\s*\d+", " ", stem)

    # Remove standalone number artifacts (e.g. "2-2", "-2", " 2 ")
    work = re.sub(r"(?<![a-zA-Z])\d+(?:-\d+)?(?![a-zA-Z])", " ", work)
    work = re.sub(r"[-_]+", " ", work)
    work = re.sub(r"\s+", " ", work).strip()

    text = work.lower()

    # 2. Match host stone
    host_key, host_val = find_in_dict(text, HOST_STONES)
    if host_key:
        text = re.sub(r"(?<![a-z])" + re.escape(host_key) + r"(?![a-z])", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

    # 3. Match origin
    origin_key, origin_val = find_in_dict(text, ORIGINS)
    if origin_key:
        text = re.sub(r"(?<![a-z])" + re.escape(origin_key) + r"(?![a-z])", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

    # 4. Match treatment
    treat_key, treat_val = find_in_dict(text, TREATMENTS)
    if treat_key:
        text = re.sub(r"(?<![a-z])" + re.escape(treat_key) + r"(?![a-z])", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

    # 5. Whatever remains = inclusion type
    inclusion_en_raw = re.sub(r"\s+", " ", text).strip()
    inclusion_en = inclusion_en_raw.title() if inclusion_en_raw else ""
    inclusion_fr = translate_inclusion(inclusion_en_raw) if inclusion_en_raw else "Non identifié"

    # 6. Diagnostic note
    diag_lookup_key = (host_key or "", inclusion_en_raw.lower() if inclusion_en_raw else "")
    diag = DIAGNOSTICS.get(diag_lookup_key, DIAG_DEFAULT)

    return {
        "original_name": path.name,
        "ext":           real_suffix(path),
        "host_key":      host_key or "",
        "host_fr":       host_val["fr"] if host_val else "Non identifié",
        "host_en":       host_val["en"] if host_val else "Unidentified",
        "origin_key":    origin_key or "",
        "origin_fr":     origin_val["fr"] if origin_val else "Non identifiée",
        "origin_en":     origin_val["en"] if origin_val else "Not identified",
        "treat_fr":      treat_val["fr"] if treat_val else "Aucun détecté",
        "treat_en":      treat_val["en"] if treat_val else "None detected",
        "inclusion_en":  inclusion_en,
        "inclusion_fr":  inclusion_fr,
        "magnification": magnification,
        "diag_fr":       diag["fr"],
        "diag_en":       diag["en"],
    }


# ─── SLUG & TITLE ──────────────────────────────────────────────────────────────

def build_slug(data: dict) -> str:
    parts = [
        data["inclusion_en"].lower(),
        data["host_key"],
        data["origin_key"],
    ]
    return slugify(" ".join(p for p in parts if p))


def build_title(data: dict, lang: str) -> str:
    if lang == "fr":
        inc    = data["inclusion_fr"] or "Inclusion"
        host   = data["host_fr"]
        origin = data["origin_fr"]
        treat  = data["treat_fr"]
        no_host   = not host  or host  == "Non identifié"
        no_origin = not origin or origin == "Non identifiée"
        in_prep   = "dans"
        sep       = " — "
    else:
        inc    = data["inclusion_en"] or "Inclusion"
        host   = data["host_en"]
        origin = data["origin_en"]
        treat  = data["treat_en"]
        no_host   = not host  or host  == "Unidentified"
        no_origin = not origin or origin == "Not identified"
        in_prep   = "in"
        sep       = " — "

    title = inc
    if not no_host:
        title += f" {in_prep} {host}"
        neutral_treats = {"Aucun détecté", "Non chauffé", "None detected", "Unheated"}
        if treat and treat not in neutral_treats:
            title += f" ({treat.lower()})"
    if not no_origin:
        title += f"{sep}{origin}"
    return title


# ─── MARKDOWN GENERATION ───────────────────────────────────────────────────────

def build_frontmatter(data: dict, title: str, lang: str) -> str:
    if lang == "fr":
        fields = {
            "pierre_hote":         data["host_fr"],
            "type_inclusion":      data["inclusion_fr"],
            "origine":             data["origin_fr"],
            "traitement":          data["treat_fr"],
            "interet_diagnostique": data["diag_fr"],
        }
    else:
        fields = {
            "pierre_hote":         data["host_en"],
            "type_inclusion":      data["inclusion_en"],
            "origine":             data["origin_en"],
            "traitement":          data["treat_en"],
            "interet_diagnostique": data["diag_en"],
        }

    lines = [
        "---",
        f'title: "{title}"',
        f"date: {TODAY}",
        "draft: false",
    ]
    for key, val in fields.items():
        if key == "interet_diagnostique":
            if data["magnification"]:
                lines.append(f'grossissement: "{data["magnification"]}"')
        lines.append(f'{key}: "{val}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


# ─── FILE OPERATIONS ───────────────────────────────────────────────────────────

_used_slugs: set[str] = set()


def unique_slug(base: str) -> str:
    slug, n = base, 2
    while slug in _used_slugs:
        slug = f"{base}-{n}"
        n += 1
    _used_slugs.add(slug)
    return slug


def process_photo(photo_path: Path) -> dict:
    data  = parse_photo(photo_path)
    slug  = unique_slug(build_slug(data))
    data["slug"] = slug

    if MULTILINGUAL:
        targets = [
            (REPO_DIR / "content" / "fr" / "inclusions" / slug, "fr"),
            (REPO_DIR / "content" / "en" / "inclusions" / slug, "en"),
        ]
    else:
        targets = [
            (REPO_DIR / "content" / "inclusions" / slug, "fr"),
        ]

    created_dirs = []
    for folder, lang in targets:
        folder.mkdir(parents=True, exist_ok=True)
        index_path = folder / "index.md"
        if index_path.exists():
            print(f"    [SKIP] {index_path.relative_to(REPO_DIR)} déjà existant")
            continue
        title   = build_title(data, lang)
        content = build_frontmatter(data, title, lang)
        index_path.write_text(content, encoding="utf-8")

        # Copy photo into the FR folder only (shared resource)
        if lang == "fr" or not MULTILINGUAL:
            photo_dest = folder / f"photo{data['ext']}"
            shutil.copy2(photo_path, photo_dest)

        created_dirs.append((folder.relative_to(REPO_DIR), lang.upper()))

    data["created"] = created_dirs
    return data


# ─── GIT ───────────────────────────────────────────────────────────────────────

def run_git():
    print("\n" + "-" * 60)
    print("Git")
    steps = [
        (["git", "-C", str(REPO_DIR), "add", "."],                              "add ."),
        (["git", "-C", str(REPO_DIR), "commit", "-m", "ajout inclusions auto"], "commit"),
        (["git", "-C", str(REPO_DIR), "push"],                                  "push"),
    ]
    for cmd, label in steps:
        print(f"  $ git {label}", end=" ... ", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            print(f"ERREUR\n  {result.stderr.strip()}")
        else:
            out = (result.stdout + result.stderr).strip()
            if out:
                print(f"OK\n    {out}")
            else:
                print("OK")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Dossier source : {PHOTO_DIR}")
    print(f"Dépôt cible    : {REPO_DIR}")
    print(f"Mode           : {'bilingue (FR + EN)' if MULTILINGUAL else 'monolinguistique (FR)'}")
    print()

    if not PHOTO_DIR.exists():
        print(f"ERREUR : dossier introuvable — {PHOTO_DIR}")
        return

    photos = sorted(
        p for p in PHOTO_DIR.iterdir()
        if p.is_file() and (p.suffix.lower() in PHOTO_EXTS
                            or Path(p.stem).suffix.lower() in PHOTO_EXTS)
    )

    if not photos:
        print("Aucune photo trouvée.")
        return

    results = []
    for photo in photos:
        print("-" * 60)
        print(f"Fichier : {photo.name}")
        data = process_photo(photo)
        results.append(data)

        w = 16
        print(f"  {'Pierre hôte':<{w}}: {data['host_fr'] or '—'}")
        print(f"  {'Type inclusion':<{w}}: {data['inclusion_fr'] or '—'}")
        print(f"  {'Origine':<{w}}: {data['origin_fr'] or '—'}")
        print(f"  {'Traitement':<{w}}: {data['treat_fr']}")
        print(f"  {'Grossissement':<{w}}: {data['magnification'] or '—'}")
        print(f"  {'Slug':<{w}}: {data['slug']}")
        for folder, lang in data["created"]:
            print(f"  ✓ {lang:<{w-2}}: {folder}")

    print("\n" + "=" * 60)
    print(f"Résumé : {len(results)} photo(s) traitée(s), "
          f"{sum(len(r['created']) for r in results)} dossier(s) créé(s).")

    run_git()
    print("\nTerminé.")


if __name__ == "__main__":
    main()
