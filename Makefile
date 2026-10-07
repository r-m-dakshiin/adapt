.PHONY: install data run nn clean

install:
	pip install -r requirements.txt

data:
	python scripts/generate_mock_data.py

nn:
	bash scripts/build_nn.sh

run:
	uvicorn app.main:app --reload --port 8000

clean:
	rm -rf __pycache__ app/__pycache__ app/*/__pycache__ .pytest_cache
