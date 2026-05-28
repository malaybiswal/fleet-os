.PHONY: reset-demo reset-demo-dry-run

reset-demo:
	docker compose exec api python -m app.seed.demo_environment $(DEMO_ARGS)

reset-demo-dry-run:
	docker compose exec api python -m app.seed.demo_environment --dry-run $(DEMO_ARGS)
