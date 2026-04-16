# AKS Auto Key iPhone Web App — Easy Deploy

This package is set up for the easiest realistic deployment path.

## What you still need
You **cannot** run the Python backend directly in Safari on iPhone.
You need **one** hosting account and **one** code repo.

The easiest path is:
1. Create a public GitHub repo
2. Upload these files
3. In Render, click **New + → Blueprint** or **Web Service**
4. Connect the repo
5. Add `OPENAI_API_KEY`
6. Deploy
7. Open the live link in Safari and tap **Add to Home Screen**

## Fast deploy settings
This repo already includes `render.yaml`, so Render can read the settings automatically.

### Render settings
- Environment: `Python`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variable: `OPENAI_API_KEY`

## Exact 5-minute flow
### 1) Unzip this package
On iPhone, tap the ZIP in Files to extract it.

### 2) Upload everything inside to GitHub
Create a new public repo and upload all files.

### 3) Deploy on Render
- Sign in to Render
- Click **New +**
- Choose **Web Service**
- Connect your GitHub repo
- Render should detect the app settings automatically from `render.yaml`
- Add `OPENAI_API_KEY` in Environment
- Click Deploy

### 4) Use on iPhone
- Open the Render URL in Safari
- Tap **Share**
- Tap **Add to Home Screen**

## What if you do not add an API key?
The app still runs in fallback mode and produces basic copy, but the AI image-based generation will not work.

## Honest limitation
There is no safe way to run this exact AI app fully on iPhone in Safari with **no** hosting, because the API key must stay on a backend.

## Local computer run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python app.py
```
