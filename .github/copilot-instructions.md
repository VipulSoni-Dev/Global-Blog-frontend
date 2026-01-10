<!-- Copilot / AI agent instructions for Globe Blog (Astro) -->
# Repo snapshot

- Project type: Static site built with Astro (blog template).
- Key runtime: Static site generation using `astro:content` for blog collections and `astro:assets` for images.

# Purpose for AI agents

This file gives focused, actionable knowledge to help AI coding agents be productive immediately in this repository.

# Big picture (what matters)

- Content-driven Astro site. Blog posts live as Markdown/MDX under `src/content/blog/` and are type-checked by `src/content.config.ts`.
- Pages and routes are standard Astro files in `src/pages/`. The blog uses a dynamic route at `src/pages/blog/[...slug].astro` which expects collection entries from `getCollection('blog')`.
- Article rendering is handled by `src/layouts/BlogPost.astro` which expects frontmatter fields such as `title`, `description`, `pubDate`, optional `updatedDate`, `heroImage` (object with `src` and `alt`) and `tags`.

# Important files to inspect

- `astro.config.mjs` — Astro configuration.
- `src/content.config.ts` — collection definitions and frontmatter schema (authoritative source for fields and types).
- `src/content/blog/` — Markdown/MDX posts (frontmatter examples).
- `src/layouts/BlogPost.astro` — canonical rendering of a post (uses `Image` from `astro:assets`).
- `src/pages/blog/[...slug].astro` — how posts are routed and rendered.
- `src/pages/rss.xml.js` — RSS generation using `@astrojs/rss` and `getCollection('blog')`.
- `src/consts.ts` — global constants used by RSS and head components.
- `src/styles/global.css` — global styling; small project-specific CSS conventions.

# Content/frontmatter conventions (concrete examples)

- Typical frontmatter (see `src/content/blog/*.mdx`):

  ```yaml
  title: string
  description: string
  blogName: string (optional)
  pubDate: ISO-like string (parsed via `z.coerce.date()`)
  updatedDate: optional (parsed via `z.coerce.date()`)
  heroImage:
    src: relative path (uses `image()` loader in `content.config.ts`)
    alt: string
  tags: array[string]
  lang: optional locale string (e.g. en)
  ```

- Implementation notes: `src/content.config.ts` uses `z.coerce.date()` so dates must be parseable by JavaScript Date.
- `heroImage.src` should be compatible with the `image()` loader (paths usually relative to the content file, e.g. `../../assets/...`).

# Code patterns

- Use `getCollection('blog')` to list posts. Example: `const posts = await getCollection('blog')` (used in routing and RSS).
- To render content in a page route, use `render()` from `astro:content`, then pass the `Content` into a layout slot (see `src/pages/blog/[...slug].astro`).
- The `BlogPost` layout expects `post.data` props and places the rendered `Content` in a slot.

# Build / dev / debug commands

- Run from repository root.
- Common commands (see `README.md`):

  - `npm install` — install dependencies
  - `npm run dev` — start dev server (default port shown by Astro)
  - `npm run build` — generate production `./dist`
  - `npm run preview` — preview build locally

- There are no project-specific test harnesses or custom build scripts in the repo; follow the above Astro commands.

# Integration / external dependencies

- Uses `@astrojs/rss` for RSS and relies on Astro's `astro:content` and `astro:assets` (Image) features.
- Content images referenced in frontmatter rely on the `image()` loader declared in `src/content.config.ts`.

# When changing schema or content

- If you change frontmatter fields, update `src/content.config.ts` immediately (it is the source of truth). Tests aren't present here, so schema mismatches will show up at build/dev time.
- When adding images referenced by content, put them in `src/assets/` and use relative paths in frontmatter that match the `image()` loader expectations.

# Quick heuristics for code edits

- Small content or layout tweaks: edit `src/content/blog/*` or `src/layouts/BlogPost.astro`.
- Routing/collection changes: edit `src/content.config.ts` and `src/pages/blog/[...slug].astro` together.
- Global text/labels: `src/consts.ts`.

# Examples to reference

- Rendering pipeline: `src/pages/blog/[...slug].astro` → `getCollection('blog')` → `render(post)` → `src/layouts/BlogPost.astro`.
- RSS: `src/pages/rss.xml.js` uses `getCollection('blog')` and `src/consts.ts`.

# What I (the AI) should not assume

- There are no unit tests or CI configs to infer workflows; avoid adding tests unless requested.
- No special environment variables or secret integrations are present.

# How to propose changes

- When modifying schema or content structure, include a short note explaining the semantic reason and the files changed (`src/content.config.ts`, affected MDX files, and layout).

---

If anything here is unclear or you'd like more detail (example PR, automated checks, or CI suggestions), tell me which area to expand. 
