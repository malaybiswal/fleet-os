.PHONY: reset-demo reset-demo-dry-run demo-reset ingest-geotab poll-geotab-demo demo-geotab demo-simulator demo-both

reset-demo:
	docker compose exec api python -m app.seed.demo_environment $(DEMO_ARGS)

reset-demo-dry-run:
	docker compose exec api python -m app.seed.demo_environment --dry-run $(DEMO_ARGS)

demo-reset:
	docker compose exec api python -m app.jobs.demo_live_fleet_reset $(RESET_ARGS)

ingest-geotab:
	docker compose exec api python -m app.jobs.geotab_telemetry_ingestion $(GEOTAB_ARGS)

poll-geotab-demo:
	docker compose exec api python -m app.jobs.geotab_telemetry_ingestion --poll $(GEOTAB_ARGS)

demo-geotab:
	docker compose exec api python -m app.jobs.demo_live_fleet_reset $(RESET_ARGS)
	docker compose exec api python -m app.jobs.geotab_telemetry_ingestion --poll $(GEOTAB_ARGS)

demo-simulator:
	docker compose exec api python -m app.jobs.demo_live_fleet_reset $(RESET_ARGS)
	docker compose exec api python -m app.jobs.simulator_telemetry_ingestion --poll $(SIMULATOR_ARGS)

demo-both:
	@set -e; \
	docker compose exec api python -m app.jobs.demo_live_fleet_reset $(RESET_ARGS); \
	docker compose exec -T api python -m app.jobs.geotab_telemetry_ingestion --poll $(GEOTAB_ARGS) & \
	geotab_pid=$$!; \
	docker compose exec -T api python -m app.jobs.simulator_telemetry_ingestion --poll $(SIMULATOR_ARGS) & \
	simulator_pid=$$!; \
	trap 'kill $$geotab_pid $$simulator_pid 2>/dev/null; wait $$geotab_pid $$simulator_pid 2>/dev/null' INT TERM EXIT; \
	wait $$geotab_pid $$simulator_pid
