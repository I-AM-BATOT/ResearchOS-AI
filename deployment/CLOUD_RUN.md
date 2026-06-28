# Deploying to Google Cloud Run

ResearchOS AI ships as two independently deployable services: the Streamlit
frontend and the MCP server. You can deploy either or both to Cloud Run.

## 1. Prerequisites
- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated: `gcloud auth login`
- Artifact Registry (or Container Registry) enabled

## 2. Set project variables
```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
gcloud config set project "$PROJECT_ID"
```

## 3. Deploy the Streamlit app
```bash
gcloud run deploy researchos-ai \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --port 8501 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY,GEMINI_MODEL=gemini-2.5-flash
```
Cloud Run's `--source .` build will use the root `Dockerfile`... if you keep the
Dockerfile in `deployment/`, point Cloud Build at it explicitly instead:
```bash
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/researchos/app" \
  -f deployment/Dockerfile .
gcloud run deploy researchos-ai \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/researchos/app" \
  --region "$REGION" --allow-unauthenticated --port 8501 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY
```

## 4. Deploy the MCP server (optional, separate service)
```bash
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/researchos/mcp" \
  -f deployment/Dockerfile.mcp .
gcloud run deploy researchos-mcp \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/researchos/mcp" \
  --region "$REGION" --allow-unauthenticated --port 8765
```

## 5. Environment variables
Set every variable from `.env.example` via `--set-env-vars` or, for secrets like
`GEMINI_API_KEY`, prefer Secret Manager:
```bash
gcloud secrets create gemini-api-key --data-file=- <<< "$GEMINI_API_KEY"
gcloud run deploy researchos-ai --update-secrets=GEMINI_API_KEY=gemini-api-key:latest ...
```

## 6. Persistent memory note
Cloud Run instances are stateless/ephemeral by default — local SQLite/ChromaDB
files written to `.researchos_memory/` will NOT persist across deployments or
instance restarts. For production persistence, mount a Cloud Storage FUSE
volume or point `MEMORY_DIR` at a Filestore/Cloud SQL-backed path, or swap the
SQLite backend for a managed vector DB (e.g. Vertex AI Vector Search).
