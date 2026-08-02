.PHONY: setup dev format lint typecheck test test-e2e build seed-demo

setup:
	npm run setup

dev:
	npm run dev

format:
	npm run format

lint:
	npm run lint

typecheck:
	npm run typecheck

test:
	npm run test

test-e2e:
	npm run test:e2e

build:
	npm run build

seed-demo:
	npm run seed:demo

