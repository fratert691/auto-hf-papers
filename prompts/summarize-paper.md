# Paper Summary Prompt

For each paper in the JSON, write a concise section using this structure:

## [Paper Title]

**Upvotes:** {upvotes} | **GitHub:** {stars} stars ([repo link]({githubRepo})) — or omit GitHub line if no repo

**TL;DR:** One sentence capturing the core contribution.

**What they did:** 2-3 sentences describing the method or approach. Be specific — mention the technique name, what problem it solves, and what makes it different from prior work.

**Why it matters:** 1-2 sentences on real-world impact or why the research direction is important.

**Keywords:** `keyword1` `keyword2` `keyword3`

**Links:** [HuggingFace]({hfUrl}) | [arXiv]({arxivUrl}) {| [Code]({githubRepo}) if available}

---

Rules:
- Use only content from the paper's abstract and ai_summary fields in the JSON. Do NOT visit external URLs or fabricate information.
- Always include the HuggingFace and arXiv links.
- Only include a GitHub/Code link if githubRepo is non-null in the JSON.
- Keep each paper section under 150 words total.
- Do not editorialize or use hype words like "revolutionary", "groundbreaking", "game-changer".
- Use plain language. Assume the reader is a technical ML practitioner.
