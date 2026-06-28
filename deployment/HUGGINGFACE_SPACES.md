# Deploying to Hugging Face Spaces

1. Create a new Space at https://huggingface.co/new-space
2. Choose **Streamlit** as the Space SDK
3. Push this repository's contents to the Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/researchos-ai
   git push space main
   ```
4. In the Space settings, add a secret:
   - `GEMINI_API_KEY` = your Gemini API key
   (Leave it unset to run the Space in MOCK/offline-demo mode.)
5. The Space will auto-detect `app.py` as the entry point. Make sure
   `requirements.txt` is at the repo root (it already is).
6. Hugging Face Spaces free tier has ephemeral storage — see the same
   persistence caveat as Cloud Run above; for a demo/competition Space this
   is fine, since ChromaDB/SQLite will simply reset on Space restart.
