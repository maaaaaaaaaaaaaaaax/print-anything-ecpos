# formatting

Pure functions that turn content into pixels and text lines. No I/O except reading bundled fonts. Depends on `kernel` only.

## Ported from the earlier printer module

| Module | Origin | Notes |
| --- | --- | --- |
| `raster_text.py` | `complex_text.py` | `render_spans(spans, style)` draws styled runs into a grayscale strip. Shared baseline across mixed sizes, advance widths via `getlength`, font metrics for line height, caller styles never mutated |
| `font_catalog.py` | font handling in `complex_text.py` | Typed `load_font(family, variant, size)`, cached. Families: `sans` (Inter), `serif` (Noto Serif), `monospace` (JetBrains Mono). The old `sans-b` family referenced files that were never shipped and is gone |
| `images.py` | `image.py` | `fit_within`, `rotate`, `pad_horizontal`, `to_one_bit`. Dithers: `floyd_steinberg`, `threshold`, `ordered` (4x4 Bayer). The old config named a halftone dither but never used it |
| `text_normalization.py` | new | `normalize_text`: line endings to `\n`, Unicode to NFC. Used by `render_spans` and `wrap_text`. Decomposed umlauts otherwise print as `u?` in native mode, and a bare carriage return crashed the raqm layout engine |
| `text_layout.py` | `layout.py` | `wrap_text`, `align_line`, `rule`, `two_columns`, `table_row`, `boxed`. Return lines instead of joined strings |
| `fonts/` | `fonts/` | Twelve TTF files plus `licenses/`, package data. Fonts load with Pillow's basic layout engine so output is identical on every machine |

Dropped: URL and base64 image loading (belongs to `ingest`), the `ImageLayout` duplicate, the chained `TextFormatter`.

## Planned

- `config.py`: `FormatConfig`, including `text_mode` (`native` default, `raster` by option, never mixed within a job)
- `settings.py`: the setting registry used by `/set`, `/settings` and caption parsing
- `layout.py`: `plan(document, config, profile, assets) -> PrintPlan`, plus the length estimate
- native text layout: wrapping to the profile's columns, size multipliers for headings

## Rules

- Everything here is a pure function or a frozen value.
- Dot width, columns and dpi come from `PrinterProfile`, never from constants.

## Known limits of raster text

Glyphs missing from the bundled fonts render as an empty box. Coverage checked for the regular weights: Inter lacks box-drawing characters, Noto Serif lacks the check mark and cross, JetBrains Mono covers all of these. None of the three cover CJK or emoji. A fallback font chain is a possible later addition.
