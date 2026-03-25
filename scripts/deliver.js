#!/usr/bin/env node

// ============================================================================
// HuggingFace Daily Papers — Delivery Script
// ============================================================================
// Sends the generated digest to the user's configured delivery method.
// Supports: stdout (default), Telegram, Email (via Resend API).
//
// Usage:
//   echo "digest text" | node deliver.js
//   node deliver.js --message "digest text"
//   node deliver.js --file /path/to/digest.txt
//
// Config from: ~/.hf-papers/config.json  (local use)
// API keys from: ~/.hf-papers/.env       (local use)
//
// In GitHub Actions, all config is read from environment variables:
//   DELIVERY_METHOD=email
//   TO_EMAIL=you@example.com
//   RESEND_API_KEY=re_xxx
//   TELEGRAM_BOT_TOKEN=xxx
//   TELEGRAM_CHAT_ID=xxx
// ============================================================================

const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.hf-papers');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');
const ENV_FILE = path.join(CONFIG_DIR, '.env');

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    }
  } catch (e) {}
  return { deliveryMethod: 'stdout' };
}

function loadEnv() {
  const env = {};
  try {
    if (fs.existsSync(ENV_FILE)) {
      const lines = fs.readFileSync(ENV_FILE, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx > 0) {
          env[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
        }
      }
    }
  } catch (e) {}
  return env;
}

async function readInput() {
  const args = process.argv.slice(2);

  const msgArg = args.find(a => a.startsWith('--message='));
  if (msgArg) return msgArg.split('=').slice(1).join('=');

  const fileArg = args.find(a => a.startsWith('--file='));
  if (fileArg) {
    const filePath = fileArg.split('=').slice(1).join('=');
    return fs.readFileSync(filePath, 'utf8');
  }

  // Read from stdin
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

// Telegram: split into chunks respecting 4096 char limit
async function sendTelegram(text, token, chatId) {
  const MAX = 4000;
  const chunks = [];
  let remaining = text;
  while (remaining.length > 0) {
    if (remaining.length <= MAX) {
      chunks.push(remaining);
      break;
    }
    // Split at last newline before MAX
    const cut = remaining.lastIndexOf('\n', MAX);
    if (cut > 0) {
      chunks.push(remaining.slice(0, cut));
      remaining = remaining.slice(cut + 1);
    } else {
      chunks.push(remaining.slice(0, MAX));
      remaining = remaining.slice(MAX);
    }
  }

  for (const chunk of chunks) {
    const url = `https://api.telegram.org/bot${token}/sendMessage`;
    let res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: chunk, parse_mode: 'Markdown' })
    });

    if (!res.ok) {
      // Retry without Markdown formatting if it fails
      res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId, text: chunk })
      });
    }

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Telegram API error: ${res.status} ${body}`);
    }
  }
}

async function sendEmail(text, apiKey, toEmail) {
  const today = new Date().toISOString().split('T')[0];
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      from: 'HF Papers Digest <digest@resend.dev>',
      to: [toEmail],
      subject: `HuggingFace Papers Digest — ${today}`,
      text
    })
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Resend API error: ${res.status} ${body}`);
  }
}

async function main() {
  const config = loadConfig();
  const env = loadEnv();
  const text = await readInput();

  if (!text.trim()) {
    process.stdout.write(JSON.stringify({ status: 'error', message: 'No content to deliver' }) + '\n');
    process.exit(1);
  }

  // Env vars take priority over config file — enables GitHub Actions usage
  const method = process.env.DELIVERY_METHOD || config.deliveryMethod || 'stdout';

  try {
    if (method === 'telegram') {
      const token = process.env.TELEGRAM_BOT_TOKEN || env.TELEGRAM_BOT_TOKEN;
      const chatId = process.env.TELEGRAM_CHAT_ID || config.telegram?.chatId;
      if (!token) throw new Error('TELEGRAM_BOT_TOKEN not set');
      if (!chatId) throw new Error('TELEGRAM_CHAT_ID not set');
      await sendTelegram(text, token, chatId);
      process.stdout.write(JSON.stringify({ status: 'ok', method: 'telegram' }) + '\n');

    } else if (method === 'email') {
      const apiKey = process.env.RESEND_API_KEY || env.RESEND_API_KEY;
      const toEmail = process.env.TO_EMAIL || config.email?.address;
      if (!apiKey) throw new Error('RESEND_API_KEY not set');
      if (!toEmail) throw new Error('TO_EMAIL not set');
      await sendEmail(text, apiKey, toEmail);
      process.stdout.write(JSON.stringify({ status: 'ok', method: 'email' }) + '\n');

    } else {
      // stdout
      process.stdout.write(text + '\n');
    }
  } catch (e) {
    process.stderr.write(JSON.stringify({ status: 'error', message: e.message }) + '\n');
    process.exit(1);
  }
}

main().catch(e => {
  process.stderr.write(`Fatal error: ${e.message}\n`);
  process.exit(1);
});
