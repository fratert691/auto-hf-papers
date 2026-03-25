# Translation Prompt (Chinese)

When language = "zh", translate the entire digest to Chinese.
When language = "bilingual", interleave English and Chinese paragraph by paragraph:
- Write the English paragraph first, then immediately follow with the Chinese translation of the same paragraph.
- Apply this to every paragraph including the header, TL;DR, "What they did", "Why it matters", and Keywords.
- Do NOT translate URLs, code snippets, paper IDs, or technical identifiers (e.g., model names, dataset names, method names like "MinerU-Diffusion").

Translation guidelines:
- Use standard simplified Chinese (简体中文).
- Keep technical terms in English the first time they appear in a section, followed by a Chinese explanation if needed. For example: "diffusion model（扩散模型）".
- Translate naturally — do not do word-for-word translation. Preserve the technical meaning.
- Section headers like "TL;DR", "What they did", "Why it matters", "Keywords", "Links" should be translated as: "一句话总结"、"方法"、"意义"、"关键词"、"链接".
