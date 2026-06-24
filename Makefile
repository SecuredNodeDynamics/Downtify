#!make

DOWNTIFY_VERSION := 2.10.59
TARGET := ghcr.io/securednodedynamics/downtify

all: build latest

build:
	docker buildx create --use
	docker buildx build --platform=linux/amd64,linux/arm64 -t $(TARGET):$(DOWNTIFY_VERSION) --push .

latest:
	docker buildx create --use
	docker buildx build --platform=linux/amd64,linux/arm64 -t $(TARGET):latest --push .

clean:
	find downloads -type f -name "*.mp3" -exec rm -f {} \;

up:
	docker compose up --build -d

down:
	docker compose down

run:
	uv run python main.py web

format:
	uv run ruff format .; uv run ruff check . --fix
	./frontend/node_modules/.bin/prettier --write frontend/src/.

lint:
	./frontend/node_modules/.bin/prettier --check frontend/src/.
	uv run ruff check .; uv run ruff check . --diff

export:
	uv export --no-hashes --no-dev -o requirements.txt

changelog:
	github_changelog_generator -u henriquesebastiao -p downtify -o CHANGELOG --no-verbose
	@echo "Changelog generated at CHANGELOG"

test:
	npm run test --prefix frontend
	uv run pytest -x -s -v

android-apk:
	bash scripts/build-android-apk.sh

publish:
	bash scripts/publish.sh $(word 2,$(MAKECMDGOALS))

version:
	@VERSION=$(word 2,$(MAKECMDGOALS)); \
	if [ -z "$$VERSION" ]; then VERSION=patch; fi; \
	echo "Downtify version bump: $$VERSION"; \
	node version.js $$VERSION
	npm install --prefix frontend
	npm run build --prefix frontend
	uv run ruff format .; uv run ruff check . --fix
	./frontend/node_modules/.bin/prettier --write frontend/src/.

doc:
	uv run zensical serve

%:
	@:

.PHONY: all build latest clean up down run format lint export changelog version doc android-apk publish
