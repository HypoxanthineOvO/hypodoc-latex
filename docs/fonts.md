# Hypo-LaTeX Chinese Font Roles

Hypo-LaTeX uses theme-level font roles instead of asking ordinary Markdown files to set fonts directly. AI-authored drafts should usually select only `theme`.

## Font Roles

- Body: long paragraphs, tables, ordinary lists, and mixed Chinese/English text.
- Title: cover titles, chapter titles, and large visual headings.
- Mono: code, commands, paths, model IDs, and compact technical tokens.
- Poster title: optional future role for strong cover-only titles such as Smiley Sans or DingTalk JinBuTi.

## Theme Defaults

### `classic-readable`

- Body: `Noto Serif CJK SC`
- Title / cover / chapter: `Noto Serif CJK SC Black`
- Module / Q-A title: `Noto Serif CJK SC Bold`
- Mono: `LXGW WenKai Mono`

Use this for longform books, tutorials, and paper-like Chinese reading.

### `tech-minimal`

- Body: `Noto Serif CJK SC`
- Sans fallback for explicit technical accents: `Sarasa Gothic SC`
- Title / cover / chapter: `Noto Serif CJK SC Black`
- Module / Q-A title: `Noto Serif CJK SC Bold`
- Mono: `LXGW WenKai Mono`

Use this for model reviews, technical guides, rankings, tables, and mixed model-name text when a restrained paper-like look is preferred.

### `warm-handbook`

- Body: `Noto Serif CJK SC`
- Title / cover / chapter: `Noto Serif CJK SC Black`
- Module / Q-A title: `Noto Serif CJK SC Bold`
- Mono: `LXGW WenKai Mono`

Use this for explanation-heavy or more conversational tutorials. Its warmer tone
comes from spacing and color choices; ordinary body text still uses the stable
Noto Serif role, and LXGW is kept for mono/code only.

### `academic-clean`

- Body: `Noto Serif CJK SC`
- Sans / mixed fallback: `Sarasa Gothic SC`
- Title / cover / chapter: `Noto Serif CJK SC Black`
- Module / Q-A title: `Noto Serif CJK SC Bold`
- Mono: `LXGW WenKai Mono`

Use this for formal notes, study material, and academic-style documents.

## Fallback Policy

The package checks each preferred font with `\IfFontExistsTF` before using it. Missing preferred fonts fall back to the stable Noto CJK/default LaTeX stack rather than breaking the build.

`hypolatex doctor` treats Noto CJK fonts as required fallback fonts and reports MiSans, Sarasa Gothic SC, LXGW WenKai, Smiley Sans, Alibaba PuHuiTi 3.0, and DingTalk JinBuTi as recommended Chinese fonts. Missing recommended fonts should be fixed for final visual quality, but they do not block the MVP build loop.

The current package defaults deliberately do not use MiSans, Smiley Sans, Alibaba PuHuiTi, or DingTalk JinBuTi for ordinary document boxes. MiSans looked too product-like inside cards, while the installed Alibaba/Smiley/DingTalk files are woff2 or segmented woff2 and are not stable XeLaTeX core defaults in this environment.

## AI Authoring Rules

1. For ordinary drafts, use only `theme`.
2. Use `tech-minimal` for model evaluation, technical ranking, and table-heavy content.
3. Use `classic-readable` for longform book-like tutorials.
4. Use `warm-handbook` for conversational explanations or solution walkthroughs.
5. Use `academic-clean` for formal study material.
6. Do not add `mainfont`, `sansfont`, `monofont`, or `cjkfont` unless the user explicitly requests a document-specific override.
