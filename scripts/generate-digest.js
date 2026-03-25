#!/usr/bin/env node

// ============================================================================
// HuggingFace Daily Papers — Generate Digest via Claude API
// ============================================================================
// Reads the JSON output from fetch-papers.js, calls the Anthropic Messages
// API to generate a human-readable digest, and writes it to stdout.
//
// Usage:
//   node fetch-papers.js | node generate-digest.js
//   node generate-digest.js --input=feed-papers.json
//   node generate-digest.js --input=feed-papers.json --model=claude-haiku-4-5-20251001
//
// Requires: ANTHROPIC_API_KEY in env or ~/.hf-papers/.env
// ============================================================================

const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.hf-papers');
const ENV_FILE = path.join(CONFIG_DIR, '.env');

function loadEnvFile(filePath) {
  const env = {};
  try {
    if (fs.existsSync(filePath)) {
      for (const line of fs.readFileSync(filePath, 'utf8').split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eq = trimmed.indexOf('=');
        if (eq > 0) env[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
      }
    }
  } catch (e) {}
  return env;
}

function getArg(name) {
  const match = process.argv.find(a => a.startsWith(`--${name}=`));
  return match ? match.split('=').slice(1).join('=') : null;
}

async function readInput() {
  const inputArg = getArg('input');
  if (inputArg) return fs.readFileSync(inputArg, 'utf8');

  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

async function callClaudeAPI(apiKey, model, systemPrompt, userMessage) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model,
      max_tokens: 8192,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${body}`);
  }

  const json = await res.json();
  return json.content[0].text;
}

async function main() {
  const fileEnv = loadEnvFile(ENV_FILE);
  const apiKey = process.env.ANTHROPIC_API_KEY || fileEnv.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      'ANTHROPIC_API_KEY not found.\n' +
      'Set it as an environment variable or add it to ~/.hf-papers/.env'
    );
  }

  const model = getArg('model')
    || process.env.CLAUDE_MODEL
    || 'claude-haiku-4-5-20251001';

  const rawInput = await readInput();
  const data = JSON.parse(rawInput);

  // --language flag overrides config (useful in GitHub Actions)
  const langOverride = getArg('language') || process.env.DIGEST_LANGUAGE;
  if (langOverride) data.config.language = langOverride;

  // No papers — output a plain message, no API call needed
  if (!data.papers || data.papers.length === 0) {
    process.stdout.write(
      `HuggingFace Papers Digest — ${data.date}\n\n` +
      `No papers matched today's filters (upvotes >= ${data.stats.upvoteThreshold} or ` +
      `GitHub stars >= ${data.stats.starsThreshold}).\n` +
      `${data.stats.total} papers were submitted in total.\n`
    );
    return;
  }

  // Build system prompt from loaded prompt files
  const parts = [];

  if (data.prompts.digestIntro) {
    parts.push(data.prompts.digestIntro);
  }
  if (data.prompts.summarizePaper) {
    parts.push(data.prompts.summarizePaper);
  }
  if (data.prompts.translate && data.config.language !== 'en') {
    parts.push(data.prompts.translate);
  }

  const systemPrompt = parts.join('\n\n---\n\n');

  // Build user message
  const userMessage = `Generate the digest for ${data.date}.

Language: "${data.config.language}"

Stats:
- Total papers submitted today: ${data.stats.total}
- Papers matching filters: ${data.stats.filtered}
- Upvote threshold: ${data.stats.upvoteThreshold}
- GitHub stars threshold: ${data.stats.starsThreshold}

Papers (sorted by upvotes, descending):
${JSON.stringify(data.papers, null, 2)}`;

  const digest = await callClaudeAPI(apiKey, model, systemPrompt, userMessage);
  process.stdout.write(digest);
}

main().catch(e => {
  process.stderr.write(`Error: ${e.message}\n`);
  process.exit(1);
});
