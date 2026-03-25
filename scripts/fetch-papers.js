#!/usr/bin/env node

// ============================================================================
// HuggingFace Daily Papers — Fetch & Filter Script
// ============================================================================
// Fetches papers from the HuggingFace daily papers API, filters by upvotes
// or GitHub stars, loads prompt templates, and outputs a single JSON blob
// for the LLM to process.
//
// Usage:
//   node fetch-papers.js
//   node fetch-papers.js --date=2026-03-25
//   node fetch-papers.js --upvotes=10 --stars=50
//
// Output: JSON to stdout with papers, config, prompts, and stats.
// ============================================================================

const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.hf-papers');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');
const PROMPTS_DIR = path.join(CONFIG_DIR, 'prompts');
const LOCAL_PROMPTS_DIR = path.join(__dirname, '..', 'prompts');

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name) {
  const match = args.find(a => a.startsWith(`--${name}=`));
  return match ? match.split('=').slice(1).join('=') : null;
}

const dateArg = getArg('date');
const upvotesArg = getArg('upvotes');
const starsArg = getArg('stars');

function getTodayDate() {
  return new Date().toISOString().split('T')[0];
}

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    }
  } catch (e) {
    // ignore, use defaults
  }
  return {};
}

function loadPrompt(name) {
  // 3-tier priority: user custom > local project copy
  const userPath = path.join(PROMPTS_DIR, `${name}.md`);
  const localPath = path.join(LOCAL_PROMPTS_DIR, `${name}.md`);

  if (fs.existsSync(userPath)) {
    return fs.readFileSync(userPath, 'utf8').trim();
  }
  if (fs.existsSync(localPath)) {
    return fs.readFileSync(localPath, 'utf8').trim();
  }
  return null;
}

async function fetchDailyPapers(date) {
  const url = `https://huggingface.co/api/daily_papers?date=${date}`;
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' }
  });
  if (!res.ok) {
    throw new Error(`HuggingFace API returned ${res.status} for date ${date}`);
  }
  return res.json();
}

async function main() {
  const config = loadConfig();

  const date = dateArg || getTodayDate();
  const upvoteThreshold = parseInt(upvotesArg ?? config.upvoteThreshold ?? 20, 10);
  const starsThreshold = parseInt(starsArg ?? config.githubStarsThreshold ?? 100, 10);

  let rawPapers;
  const errors = [];

  try {
    rawPapers = await fetchDailyPapers(date);
  } catch (e) {
    errors.push(`Failed to fetch papers: ${e.message}`);
    process.stdout.write(JSON.stringify({
      date,
      config: { language: config.language || 'en', deliveryMethod: config.deliveryMethod || 'stdout' },
      stats: { total: 0, filtered: 0, upvoteThreshold, starsThreshold },
      papers: [],
      prompts: {},
      errors
    }, null, 2));
    process.exit(0);
  }

  // Filter: upvotes >= threshold OR githubStars >= threshold
  const filtered = rawPapers
    .filter(item => {
      const p = item.paper;
      const upvotes = p.upvotes || 0;
      const stars = p.githubStars || 0;
      return upvotes >= upvoteThreshold || stars >= starsThreshold;
    })
    .map(item => {
      const p = item.paper;
      return {
        id: p.id,
        title: p.title,
        upvotes: p.upvotes || 0,
        githubRepo: p.githubRepo || null,
        githubStars: p.githubStars || 0,
        abstract: p.summary || null,
        aiSummary: p.ai_summary || null,
        keywords: p.ai_keywords || [],
        authors: (p.authors || []).map(a => a.name).filter(Boolean),
        publishedAt: p.publishedAt,
        hfUrl: `https://huggingface.co/papers/${p.id}`,
        arxivUrl: `https://arxiv.org/abs/${p.id}`,
        // flags for why it was included
        includedFor: [
          ...(p.upvotes >= upvoteThreshold ? [`upvotes=${p.upvotes}`] : []),
          ...(p.githubStars >= starsThreshold ? [`github_stars=${p.githubStars}`] : []),
        ]
      };
    });

  // Sort by upvotes desc
  filtered.sort((a, b) => b.upvotes - a.upvotes);

  const output = {
    date,
    config: {
      language: config.language || 'en',
      deliveryMethod: config.deliveryMethod || 'stdout',
    },
    stats: {
      total: rawPapers.length,
      filtered: filtered.length,
      upvoteThreshold,
      starsThreshold,
    },
    papers: filtered,
    prompts: {
      summarizePaper: loadPrompt('summarize-paper'),
      digestIntro: loadPrompt('digest-intro'),
      translate: loadPrompt('translate'),
    },
    errors,
  };

  process.stdout.write(JSON.stringify(output, null, 2));
}

main().catch(e => {
  process.stderr.write(`Fatal error: ${e.message}\n`);
  process.exit(1);
});
