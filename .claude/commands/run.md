Rebuild and start the fleet-os stack using Docker Compose.

Run the following steps in order:

1. From the project root (`/Users/pri/Projects/Git/fleet-os`), run:
   ```
   docker compose up --build -d
   ```
   This rebuilds any changed images and starts all services (db, api, frontend) in detached mode.

2. Wait for all services to be healthy, then report their status:
   ```
   docker compose ps
   ```

3. Print the URLs the stack is now reachable on:
   - Frontend: http://localhost:3000
   - API:      http://localhost:8000
   - API docs: http://localhost:8000/docs

If any service fails to start, show its logs:
```
docker compose logs <service>
```
