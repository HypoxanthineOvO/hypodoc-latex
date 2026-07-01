# Hypo-LaTeX Cover Layouts

This note records the reusable cover structures extracted from the reference image set. The goal is not to copy every visible cover. Hypo-LaTeX keeps a small layout vocabulary that AI authors can choose from when the default theme cover is not enough.

## Metadata

```yaml
---
theme: classic-readable
cover_layout: integrated-art
cover_image: assets/cover.png
---
```

- `cover_layout` selects the cover structure. Omit it for the theme default.
- `cover_image` selects a project-local image. Omit it to let the theme use its packaged default cover image when it has one.
- `title`, `subtitle`, `abstract`, `author`, `organization`, `course`, and `date` feed the visible text blocks.
- `version` is metadata only and is not printed on the cover.

## Layout Set

### `plain`

Baseline text cover. Use this for debug builds, minimal drafts, or documents where a visual cover would distract from the content.

Reference pattern: simple title page with title, subtitle, abstract, author, and date.

### `full-bleed-card`

Full-bleed image background with solid title, abstract, and author cards. This is the safest template when the background image is visually rich because it creates explicit title safety zones.

Reference pattern: illustrated novel covers and full-page landscape covers, but with stronger readable cards than the reference image usually shows.

Best for:

- longform tutorials with generated editorial art
- book-like PDFs where the cover image should remain the first visual signal
- cases where title/background overlap would otherwise reduce contrast

### `integrated-art`

Full-bleed cover artwork with built-in empty text zones. LaTeX prints the title, subtitle, abstract, author, and date directly into the clean areas instead of drawing separate white cards.

Reference pattern: complete editorial book covers where illustration, paper texture, and title space are designed together.

Best for:

- final longform books with generated cover art
- Chinese tutorial PDFs where text must remain real LaTeX text
- cases where external white cards look disconnected from the background

This is the default cover layout for `classic-readable`.

### `top-title-image`

Clean title area first, image below, abstract card near the lower section. This is the most conservative longform book structure because the title never sits directly on top of a busy image.

Reference pattern: covers with a quiet title band and a lower landscape or illustration area.

Best for:

- classic readable books
- tutorial PDFs
- final user-facing longform documents where title clarity matters more than immersion

### `info-panel`

Structured information panel with large title, summary block, author/date, and accent rules. This intentionally avoids decorative full-bleed art.

Reference pattern: blue/red exam books, guidebooks, and professional training material with checklist-like hierarchy.

Best for:

- exam review documents
- homework or project handouts
- operational guides
- structured teaching packets

### `paper-ink`

Minimal paper-and-ink cover with restrained rules, large title, and a compact abstract card. It keeps a literary or formal study feel without requiring a custom image.

Reference pattern: paper texture, line-art, and understated Chinese book covers.

Best for:

- reading notes
- formal tutorials
- study material that should feel quiet
- documents where the title itself should carry the visual weight

## Reference Image Extraction

The reference image contains many surface styles, but the reusable structures reduce to these patterns:

- large title on a clean color block
- full-bleed illustration with text over image
- top title band with image below
- vertical side title plus image field
- exam/info panel with badge, checklist, and footer band
- paper/ink cover with line art and large whitespace

Hypo-LaTeX implements the subset that is useful and stable for AI-generated PDFs. The vertical-title and badge/checklist variants are intentionally deferred until the document scenarios need dedicated metadata for side titles, badges, and bullet lists.

## AI Selection Rules

1. Use `theme` only for ordinary drafts.
2. Use `cover_layout: integrated-art` when the cover image already includes coordinated blank title and summary zones.
3. Use `cover_layout: full-bleed-card` when a generated cover image is good but text overlaps the image and no integrated text zone exists.
4. Use `cover_layout: top-title-image` when title clarity is the highest priority for a longform book.
5. Use `cover_layout: info-panel` for exam, review, assignment, project, or guide documents.
6. Use `cover_layout: paper-ink` for quiet book-like PDFs without a strong image.
7. Do not invent new layout names. If none fits, keep `cover_layout` omitted and report the mismatch.

## Template Boundary

Cover layouts are structural templates. Themes supply color tokens and visual tone. Functional document modules such as callouts, figures, questions, tables, and references should not depend on a cover layout.
