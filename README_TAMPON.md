# Dossier Tampon — Comment ajouter une inclusion

## Principe

Déposez une photo dans le dossier **`Deposer Photo/`** pendant que `watch_photos.py` tourne.
Le script détecte la photo toutes les 5 secondes, génère la page Hugo, puis supprime la photo du dossier.

---

## Lancer le watcher

```
python watch_photos.py
```

Laisser la fenêtre ouverte. Arrêter avec **Ctrl+C**.

---

## Convention de nommage

Le nom du fichier est la seule source d'information. Plus il est précis, plus la page générée est complète.

```
[inclusion]-[pierre_hote]-[origine]-[traitement]-[grossissement].[ext]
```

### Exemples

| Nom de fichier | Résultat |
|---|---|
| `fingerprint-sapphire-madagascar-unheated-x150.jpg` | Fingerprint in Corundum — Sapphire (unheated) — Madagascar |
| `apatite-spinel-tajikistan-x300.jpg` | Apatite in Spinel — Tajikistan |
| `silk-ruby-burma-x200.png` | Silk in Corundum — Ruby — Burma |
| `calcite-sapphire-siam-heated-x100.jpg` | Calcite in Corundum — Sapphire (heated) — Thailand (Siam) |
| `rosette-spinel-mada-x300.jpg` | Rosette in Spinel — Madagascar |

---

## Mots-clés reconnus

### Pierre hôte
`ruby` `sapphire` `spinel` `emerald` `alexandrite` `tourmaline` `garnet`
`peridot` `tanzanite` `zircon` `chrysoberyl` `topaz` `opal` `diamond`
`aquamarine` `tsavorite` `demantoid` `paraiba`

### Origine
`madagascar` / `mada` · `tajikistan` / `tajik` · `siam` · `thailand` / `thai`
`mozambique` · `burma` · `myanmar` · `sri lanka` · `ceylon` · `colombia`
`kashmir` · `vietnam` · `kenya` · `tanzania` · `brazil` · `australia`
`nigeria` · `cambodia` · `russia` · `china` · `pakistan` · `afghanistan`

### Traitement
`unheated` · `heated` / `heat` · `heat treated` · `no treatment`
`fracture filled` · `glass filled` · `lead glass` · `beryllium`
`diffusion` · `filled` · `oiled` · `irradiated` · `coated`

### Grossissement
`x50` `x100` `x150` `x200` `x300` `x400` (ou `X`, `×`)

### Type d'inclusion (tout ce qui reste après extraction)
`fingerprint` `silk` `rutile` `apatite` `calcite` `needle` `feather`
`cloud` `rosette` `platelet` `crystal` `zircon` `graphite` `pyrite`
`fish eye` `flux` `fracture` `healing` `veil` et tout autre terme

---

## Ce que le script crée

Pour chaque photo déposée :

```
content/inclusions/
└── fingerprint-sapphire-madagascar/
    ├── index.md      ← frontmatter Hugo (UTF-8, pas de BOM)
    └── photo.jpg     ← copie de la photo originale
```

`index.md` généré :
```yaml
---
title: "Fingerprint in Corundum — Sapphire — Madagascar"
date: 2026-06-21
draft: false
pierre_hote: "Corundum — Sapphire"
type_inclusion: "Fingerprint"
origine: "Madagascar"
traitement: "Unheated"
grossissement: "×150"
---
```

---

## Formats photo acceptés

`.jpg` `.jpeg` `.png` `.tif` `.tiff` `.webp`

---

## Conseil

Après avoir ajouté des inclusions, faites un `git add . && git commit && git push` pour publier.
