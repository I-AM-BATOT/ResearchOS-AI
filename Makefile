.PHONY: install run mcp test docker-up clean

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

mcp:
	uvicorn mcp.server:app --host 0.0.0.0 --port 8765 --reload

test:
	pytest tests/ -v --cov=. --cov-report=term-missing

docker-up:
	docker compose -f deployment/docker-compose.yml up --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .researchos_memory .test_researchos_memory
