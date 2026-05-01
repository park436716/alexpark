# LLM Wiki — 로스쿨 (Korean Law School)

A personal knowledge base of Korean law school papers, cases, and articles, following [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285) and [joonan30's adaptation](https://gist.github.com/joonan30/cbce305684d079dbe9a3fbaefe4e3959):

```
Original PDF → sources/*.md (LLM summary) → wiki/{category}/*.md (final page)
```

**Language policy**: All wiki content is in English (RAG-friendly). Conversation can be in Korean or any other language. Original Korean legal terms should be kept alongside English translations where helpful (e.g., "Constitution (헌법)").

---

## THE FOUR RULES (do not violate)

These rules are the core of the system. They prevent hallucination and keep every claim traceable.

1. **No web search.** Never use `WebSearch` or `WebFetch` to fill gaps. The point of this wiki is that every answer is grounded in papers/cases we actually have.

2. **Answer from the wiki first.** Use `sources/` and `wiki/` as the only sources of truth.

3. **If the wiki is insufficient, re-read the PDF.** Go to `papers/{author}-{year}-{words}.pdf` and extract more detail with `pypdf`. Then update the wiki.

4. **If the wiki has no paper on the topic, say so.** Tell the user *"I don't have a paper on this — please give me the PDF."* Do not improvise.

These rules apply to **every** response, including overview pages: cite only papers that exist in the wiki.

---

## Repository Structure

```
alexpark/
├── CLAUDE.md                       # This file
├── index.md                        # Page catalog
├── papers/                         # Original PDFs (cp, never symlink)
│   └── {author}-{year}-{title-5-words}.pdf
├── sources/                        # PDF summaries (English)
│   └── {author}-{year}-{title-5-words}.md
└── wiki/                           # Wiki pages (English)
    ├── constitutional-law/         # 헌법
    ├── civil-law/                  # 민법
    ├── criminal-law/               # 형법
    ├── commercial-law/             # 상법
    ├── civil-procedure/            # 민사소송법
    ├── criminal-procedure/         # 형사소송법
    ├── administrative-law/         # 행정법
    ├── concepts/                   # General doctrines, methods
    ├── overviews/                  # Synthesis pages (where compounding happens)
    └── other/                      # Cross-cutting, miscellaneous
```

## File Naming Convention

All three tiers (PDF, source, wiki) share the same stem:

```
{first-author-lastname}-{year}-{first-5-title-words}.{ext}
```

- Lowercase, special chars stripped, spaces → `-`
- Year is 4 digits
- For Korean authors, use romanized lastname (e.g., `kim-2020-...`, `lee-2019-...`)
- Court decisions: use `{court}-{year}-{case-no}.{ext}` (e.g., `scourt-2020-2019do1234.pdf`)
- Consortium / institutional papers: use the institution name

Example: `kim-2020-constitutional-review-of-emergency-decree.pdf`

## Categories

| Category | Includes (Korean / English) |
|---|---|
| `constitutional-law` | 헌법 — Constitutional law, fundamental rights, separation of powers, constitutional review |
| `civil-law` | 민법 — Civil law, contracts, torts, property, family, succession |
| `criminal-law` | 형법 — Criminal law, general principles, specific offenses |
| `commercial-law` | 상법 — Commercial law, corporations, securities, insurance, maritime |
| `civil-procedure` | 민사소송법 — Civil procedure, evidence, enforcement |
| `criminal-procedure` | 형사소송법 — Criminal procedure, investigation, trial, evidence |
| `administrative-law` | 행정법 — Administrative law, administrative litigation, regulatory law |
| `concepts` | Key doctrines, interpretive methods, comparative law concepts |
| `overviews` | Synthesis pages spanning multiple papers |
| `other` | Cross-cutting, international law, legal philosophy, miscellaneous |

Tip: classify by **legal area / doctrine**, not topic. A constitutional review of a tax statute goes to `constitutional-law` (the doctrinal lens), not to a topic-based folder.

---

## Adding a New Paper

### Step 1 — Copy PDF to `papers/` and extract text

Use `pypdf` (pure Python, no Java required):

```bash
pip3 install pypdf

python3 -c "
import pypdf, sys
reader = pypdf.PdfReader(sys.argv[1])
text = ''
for page in reader.pages[:15]:
    t = page.extract_text()
    if t: text += t + '\n'
    if len(text) > 12000: break
print(text[:12000])
" "/path/to/paper.pdf"
```

### Step 2 — Write `sources/{stem}.md`

```yaml
---
title: "Paper Title"
authors: Author List
year: YYYY
doi: DOI
category: [your-category]
pdf_path: /full/path/to/papers/{stem}.pdf
pdf_filename: {stem}.pdf
source_collection: external
---

## One-line Summary

## 1. Document Information

## 2. Key Contributions

## 3. Methodology and Architecture

## 4. Key Results and Benchmarks

## 5. Limitations and Future Work

## 6. Related Work

## 7. Glossary
```

### Step 3 — Write `wiki/{category}/{stem}.md`

```yaml
---
title: "Paper Title"
authors: Author list
year: YYYY
doi: DOI
source: {stem}.md
category: [your-category]
pdf_path: /full/path/to/papers/{stem}.pdf
pdf_filename: {stem}.pdf
source_collection: external
tags: []
---

## Summary

## Key Contributions

## Methodology and Architecture

## Results

## Related Papers

- [[category/page]] — relationship
```

### Step 4 — Update `index.md`

Add a one-line entry under the right category.

---

## PDF Management Rules

- **Always copy, never symlink.** `cp` from external locations into `papers/`.
- `pdf_path` always points inside `papers/`. Never use `~/Downloads/` or other external paths.
- `pdf_filename` must match `basename(pdf_path)`.

## Knowledge Compounding

The most valuable pages are not individual paper summaries — they are `wiki/overviews/` pages that synthesize across papers. When a question is answered well, save the answer:

> "Save this as an overview page in `wiki/overviews/`"

Each conversation should produce 5–15 new or updated wiki pages. Over time the wiki becomes a searchable, cross-referenced knowledge graph that future conversations draw from.

## Browsing with Obsidian

For visual navigation, install [Obsidian](https://obsidian.md/) (free, Mac/Windows/Linux) and open the wiki folder as a Vault. Native support for `[[wikilinks]]`, graph view, and full-text search. Obsidian only reads files, so it does not interfere with the agent's edits.

---

## Design Principles

- **3-tier**: Raw PDF (immutable) → sources/*.md → wiki/*/*.md
- **English only** in wiki content (RAG-friendly); Korean legal terms preserved in parentheses where useful
- **Obsidian compatible**: `[[wikilinks]]`, plain markdown
- **Consistent YAML**: every file has title, authors, year, doi, category, pdf_path, pdf_filename, source_collection
- **No web search**: rule #1 above

When in doubt, follow rule #1.
