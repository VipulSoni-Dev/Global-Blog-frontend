# Blog Writing Frameworks — Quick Reference

This file lists five reusable frameworks you can pick when generating blog drafts. Include the framework name in the LLM input (e.g., `"framework": "H-I-P"`) and provide `outlineHints` when you need more structure.

1) The H-I-P Framework (For High Engagement)
- Hook: Open with a bold claim, surprising stat, or relatable question.
- Insight: Explain why the topic matters and the reader's benefit.
- Promise: Tell the reader what they'll learn by the end.

Use when: You need a tight, momentum-driven feature or explainer.

2) The Listicle Framework (For Scannability)
- Intro: Define the list's scope and why items were selected.
- List: Use H2/H3 headings for each item; keep each entry consistent in form.
- Best Pick (optional): Highlight one standout item.
- Conclusion: Summarize and deliver the takeaway.

Use when: Audience skimming is expected (product roundups, tips, resources).

3) The PAS Framework (Problem–Agitate–Solution)
- Problem: Present the major pain point.
- Agitation: Amplify the consequences of inaction.
- Solution: Provide the recommended approach, tool, or mindset.

Use when: Writing persuasive how-to pieces, comparisons, or product-focused posts.

4) Hub-and-Spoke (For SEO Authority)
- Hub: A broad pillar article covering a topic comprehensively.
- Spokes: Individual deep-dive sections or standalone posts that link back to the hub.

Use when: Building topical authority and a content cluster for search.

5) The Three-Act Story (For Thought Leadership)
- Setup: Describe the context and background.
- Confrontation: The challenge or turning point.
- Resolution: How it was solved and the lesson.

Use when: Personal essays, founder stories, and lessons learned.

Pro-Tips (applies to all frameworks)
- 1-2-3 Rule: 1 idea per paragraph, ≤2 sentences per idea, and include 3 media types across the article.
- So What?: After each section ask "So what?" to ensure relevance.
- Tone & Audience: Include `tone` and `audience` in the LLM JSON to keep voice consistent.

Example JSON snippet to send to LLM
```
{
  "title": "How to Build an Audience with Short Content",
  "description": "Practical steps to grow an audience using short-form posts and consistent distribution.",
  "pubDate": "2026-01-11",
  "heroImage": {"src":"../../assets/short-content.png","alt":"Short content growth"},
  "tags": ["content","growth","short-form"],
  "framework": "H-I-P",
  "tone": "conversational",
  "audience": "creators",
  "length": "medium",
  "outlineHints": ["H2: Hook", "H2: Insight", "H2: Promise", "H2: How to start"]
}
```

Where to put generated drafts
- Generated MDX files should be saved under `src/content/blog/` and must match the frontmatter schema in `src/content.config.ts`.
