# Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public or private).
2. Go to https://share.streamlit.io and click "New app".
3. Select the repo, branch `main`, and main file path `app.py`.
4. Under "Advanced settings" → "Secrets", paste the contents of your `.env`
   in TOML format, e.g.:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```
5. Deploy. Streamlit Cloud installs `requirements.txt` automatically.
6. Note: Streamlit Cloud's filesystem is ephemeral across reboots/redeploys —
   memory (ChromaDB/SQLite) will reset, same caveat as the other platforms.
