# Intelligent Side-Channel Leakage Detection and Defense Simulator

This project provides a full local security-lab simulator with:

- FastAPI backend with PostgreSQL persistence
- WebSocket real-time metrics stream
- React dashboard for control, charts, AI risk, and defense status
- Multi-algorithm simulation: AES, ChaCha20, RSA, ECC

## One-command stack operations

### Start everything (DB + backend + frontend)

```bash
./scripts/start_stack.sh
```

This command will:

- create .env from .env.example if missing
- create/install Python environment in .venv when needed
- install frontend dependencies when needed
- start PostgreSQL via compose
- start backend and frontend in background
- start channel nodes for sender, receiver, and attacker paths
- wait until both services are reachable

Logs are written to:

- .run/backend.log
- .run/frontend.log
- .run/sender.log
- .run/receiver.log
- .run/attacker.log

### Stop everything

```bash
./scripts/stop_stack.sh
```

This command stops backend and frontend processes and stops PostgreSQL.

### Show full stack status

```bash
./scripts/status_stack.sh
```

This command shows:

- backend/frontend process state and PIDs
- sender/receiver/attacker process state and PIDs
- API and frontend URL reachability
- listening status for ports 8000, 5173, 5433, 7101, 7102, and 7103
- PostgreSQL container state
- last 20 lines from backend/frontend/channel logs

## Automated health check

Run full API and stream validation:

```bash
./scripts/health_check.sh
```

What it validates:

- frontend reachability
- sender/receiver/attacker channel reachability
- REST endpoints for simulation, metrics, attack, AI, defense, dataset export
- AI model training endpoint
- defense activate/disable cycle
- all algorithm simulation paths: AES, ChaCha20, RSA, ECC
- WebSocket frame delivery

## Algorithm simulation demo script

To run all supported security algorithms and print live metric snapshots:

```bash
./scripts/simulate_all_algorithms.sh
```

This script calls the backend API sequentially for:

- AES
- ChaCha20
- RSA
- ECC

and prints current metrics from the running simulation for each algorithm.

## Manual setup (if you prefer explicit steps)

### Backend environment

```bash
./scripts/setup_backend.sh
```

### Backend only

```bash
./scripts/run_backend.sh
```

### Frontend only

```bash
./scripts/run_frontend.sh
```

## Runtime defaults

- API base: http://localhost:8000/api/v1
- WebSocket: ws://localhost:8000/api/v1/ws/metrics
- Frontend app: http://localhost:5173
- PostgreSQL host port: 5433
- Sender channel port: 7101
- Receiver channel port: 7102
- Attacker channel port: 7103

## AI training behavior

- The backend auto-trains a RandomForest model at startup when needed.
- The backend also auto-retrains on each simulation start when AI is enabled.
- Training data is a merge of synthetic traces and stored historical traces.
- No frontend action is required for AI model training.

## Database-backed auth and payment persistence

- Login users are loaded from PostgreSQL (`payment_users` table).
- Frontend does not use hardcoded/predefined users anymore.
- Payment outcomes are stored in PostgreSQL (`payment_records` table).
- Every saved payment record is also transformed into a training trace (`trace_records` with source `payment_history`) so AI retraining continuously learns from payment behavior.

### Payment APIs

- `GET /api/v1/payments/users`
- `POST /api/v1/payments/login`
- `GET /api/v1/payments/history?limit=100`
- `POST /api/v1/payments/history`
- `GET /api/v1/payments/adaptive-policy?sender_user_id=<id>&receiver_user_id=<id>`

## Adaptive Risk Profiles

- Backend maintains per-user drift profiles in `user_risk_profiles`.
- Backend maintains sender/receiver pair policies in `pair_risk_policies`.
- Every saved payment updates both profile layers.
- Pair thresholds auto-adjust over time (`block_threshold`, `otp_threshold`, leakage thresholds).
- Frontend uses this adaptive policy at runtime to make per-pair authorization decisions.

PostgreSQL is mapped to 5433 to avoid conflicts with machines already using 5432.

## Verification commands

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests
cd frontend && npm run lint
cd frontend && npm test
cd frontend && npm run build
```
