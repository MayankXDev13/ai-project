up:
	docker compose up -d
	
down:
	docker compose down

run:
	uvicorn src.main:app --reload & python src/worker.py & wait