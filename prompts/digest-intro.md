# Digest Introduction Prompt

Begin every digest with a header like this:

---

# HuggingFace Papers Digest — {date}

**{filtered} papers** matched today's filters (upvotes >= {upvoteThreshold} or GitHub stars >= {starsThreshold}) out of {total} total papers submitted.

---

Then list all papers from highest to lowest upvotes.

If filtered = 0, output:

---

# HuggingFace Papers Digest — {date}

No papers today exceeded the thresholds (upvotes >= {upvoteThreshold}, GitHub stars >= {starsThreshold}).
{total} papers were submitted in total. Try lowering the thresholds with: `node scripts/fetch-papers.js --upvotes=5 --stars=50`

---

Rules:
- Fill in all {placeholders} from the stats object in the JSON.
- Do not add commentary beyond what is specified.
