## Blog-generation prompt template for LLMs

Purpose
- Provide a single, consistent input format to feed into an LLM so it can generate a complete blog post that fits this site's conventions (`src/content/blog`).

How to use
- Fill the JSON object below with the required fields and pass it to the LLM as context + instruction. The LLM should return a Markdown/MDX file that includes frontmatter matching the schema and the generated article content.

Required frontmatter fields (match `src/content.config.ts` schema):
- `title` (string) — full article title.
- `description` (string) — short summary for meta / list views (1–2 sentences).
- `pubDate` (ISO date string) — publication date.
- `heroImage` (object):
  - `src` (string) — relative path suggestion (e.g., `../../assets/image-name.png`).
  - `alt` (string) — alt text for accessibility.
- `tags` (array[string]) — list of tags (lowercase, hyphenated is OK).
- optional: `blogName` (string), `updatedDate` (ISO), `lang` (string)

Prompt input JSON schema
{
  "title": "...",
  "description": "...",
  "pubDate": "2025-08-23",            // ISO date
  "heroImage": {"src": "../../assets/example.png", "alt": "..."},
  "tags": ["tag1","tag2"],
  "tone": "informative | conversational | investigative | op-ed", 
  "audience": "general | developers | investors | gamers | parents | policy",
  "length": "short|medium|long",          // short ~500, medium ~900, long ~1500+
  "mustInclude": ["fact:...", "quote:...", "stat:..."],
  "avoid": ["marketing copy", "legal advice"],
  "outlineHints": ["H2: Background", "H2: Impact", "H3: Jobs", "H2: What next"],
  "examples": ["OPTIONAL: include short example paragraphs or URLs to cite"]
}

Output expectations (instructions for the LLM)
- Produce a single Markdown/MDX string that begins with frontmatter matching the schema above.
- Follow the site style: use short paragraphs, inline bullet lists, and occasional small data tables for numeric comparisons.
- Include one hero image directive in frontmatter; suggest an inline caption in the article when relevant.
- Provide a 30–40 word meta description inside `description` frontmatter.
- Generate 3–8 relevant tags.
- Provide an SEO-friendly slug suggestion derived from `title` (lowercase, hyphenated). Put suggestion in a comment block at the bottom as `<!-- slug: your-slug-here -->`.
- At the end of the article, append a `---` separator and a small author-note line: `*This article was automatically generated.*`

Article structure guidance
- Lead (1–3 short paragraphs): Hook + one-sentence summary of the situation.
- Background (H2): Provide necessary context and history.
- Current state / data (H2): Key facts, numbers, timelines, short table if helpful.
- Impact / analysis (H2): Break into sub-points (jobs, revenue, policy, consumers).
- Reactions & quotes (H2): Include named stakeholder views if available (label them clearly as paraphrases if not direct quotes).
- What’s next / outlook (H2): Predictions, scenarios, and recommended next steps.
- Quick data hits (H3): Short bullet list of points/stats.
- Final word (H2): One-paragraph takeaway and CTA (read more / subscribe / comment).

Formatting rules
- Use heading levels: H2 for main sections, H3 for sub-sections.
- Use fenced code only for small data blocks; otherwise normal markdown.
- Keep paragraphs ≤ 3 sentences where possible.
- When suggesting images, include alt text and recommended crop (e.g., `hero-wide` or `hero-square`).

Example mapping (from an existing post)
- Input fields:
  {
    "title": "India’s Online Gaming Ban 2025 — Who Wins, Who Loses...",
    "description": "India’s 2025 gaming ban explained: real-money apps suspended and the industry fallout.",
    "pubDate": "2025-08-23",
    "heroImage": {"src":"../../assets/online-gaming-ban-2025.png","alt":"India bans real-money gaming"},
    "tags": ["india-gaming","rmg-ban","esports"],
    "tone": "investigative",
    "audience": "general",
    "length": "long"
  }

- Expected output highlights:
  - Frontmatter with the fields above.
  - A short lead that calls out Dream11 / MPL suspensions.
  - A table or bullets showing state-wise fiscal impact.
  - A section listing winners (BGMI/esports) and losers (RMG startups, sponsors).
  - Quick data hits block with numeric estimates.

Prompt template (copy-paste into the LLM input area)
"""
You are a professional news/features writer. Using the following JSON input, write a blog post in MDX that fits the site's frontmatter schema and style rules.

INPUT:
<PASTE_JSON_HERE>

OUTPUT RULES:
- Start with frontmatter YAML with keys: title, description, pubDate, heroImage, tags.
- Follow Article structure guidance above.
- Keep tone as specified and length approximate.
- Provide slug suggestion in an HTML comment at the end: <!-- slug: ... -->
- Append separator and author-note.

Now generate the article.
"""

Notes & operational tips
- If the LLM fabricates specific numeric data, mark it as an estimate and prefer phrasing like "estimated" or "reported".
- For debatable policy topics, avoid legal advice — recommend consultation with experts.
- Use `mustInclude` to force inclusion of facts or sources.
