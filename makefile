.PHONY: build run format

build:
	poetry run build-exe
	move /y dist\croquis.exe croquis.exe
run:
	poetry run croquis
format:
	poetry run ruff format