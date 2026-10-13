# Run frontend and backend together

Start Docker Desktop with Linux containers. From this repository:

```powershell
docker compose --env-file .env.compose.local up --build -d
```

Open http://localhost:8081. API docs: http://localhost:8002/docs.
The local environment file is already configured on this PC and ignored by Git.
On another machine, copy `.env.compose.example` to `.env.compose.local` and set
the two absolute host paths (forward slashes work on Windows).

The first build downloads Python/Node dependencies. Backend startup loads the
locked models and data; the frontend waits for `/health` to pass. Allow several
minutes for the first build. No model training happens during startup.

```powershell
docker compose --env-file .env.compose.local ps
docker compose --env-file .env.compose.local logs --tail=100 backend
docker compose --env-file .env.compose.local down
```

Models and data are mounted read-only, excluded from build context and images.
The supplied model lock and training input hashes must match. Existing synthetic
scenario labels are preserved. LLM integration is still not connected.

The UI uses a Node server build. Browser requests use localhost:8002; server
rendering uses backend:8000 within Compose. These URLs are built into the UI;
rebuild after changing ports. This configuration is for local use, with published
ports bound to loopback. Ports 8081/8002 avoid the native app on 8080/8001.
