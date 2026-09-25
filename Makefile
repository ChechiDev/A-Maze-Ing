.PHONY: install run debug clean lint lint-strict test package

install:
	uv sync --group dev

run:
	uv run python a_maze_ing.py config.txt

debug:
	uv run python -m pdb a_maze_ing.py config.txt

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache build dist *.egg-info

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy --strict .

test:
	uv run pytest

package:
	rm -f mazegen-*.whl
	uv build --wheel --out-dir .
