# FREEDOM demo runbook — "onboarding equipment = config, not code"

Audience: Toyota CIO. Length: ~15 minutes, three beats. Everything below runs from the repo root.

| | Beat | What the audience sees | Business message |
|---|---|---|---|
| 1 | `create-node` + one `nodes.yaml` line | A new robot type (AGV) appears on the dashboard and on the plant map | Onboarding equipment for a new plant without boilerplate |
| 2 | `create-task-block` | A new "点検 (inspect)" block appears under AGV in the Job Creator toolbox | Automation capabilities usable by on-site staff, not just engineers |
| 3 | `docker compose up` + traces | Full stack from zero with one command; every step is traced in the log viewer | Repeatable site spin-up, fewer engineer-hours on triage |

## 0. Before the meeting (setup)

```bash
git clone https://github.com/akahn23/FREEDOM.git && cd FREEDOM
docker compose pull          # pre-built images (see "Live demo safety"); falls back to a local build
docker compose up            # the single start command
```

Open http://localhost:3000 and log in as `admin` / `admin123` (created automatically on first boot).
Alternatively open the repo in VS Code → "Reopen in Container" (`.devcontainer/`), which starts the same stack and
gives a terminal with Python ready for the generators.

What `docker compose up` does on first boot:

- `db`: PostgreSQL 16, creates the `auth` schema.
- `backend`: Python 3.13 venv image; reads `nodes.yaml`, creates its tables, seeds node config, serves :8080.
  It hot-reloads whenever `backend/src`, `backend/config` or `nodes.yaml` change.
- `frontend`: pre-built Next.js; runs the Better Auth migration and `scripts/seed-admin.ts`, then serves :3000.

## Beat 1 — new robot type from one command + one YAML line

> "A new plant just bought AGVs. Today, adding a robot type means an engineer hand-writes the domain model,
> runtime, repository and registration. Watch how long it takes here."

```bash
python3 scripts/create_node.py robot agv --label AGV
```

Output (abridged):

```
create-node robot.agv
  created backend/src/robot/agv/__init__.py  (5 lines)
  created backend/src/robot/agv/domain.py  (55 lines)
  created backend/src/robot/agv/node.py  (83 lines)
  created backend/src/robot/agv/repository.py  (36 lines)
  edited  backend/src/robot/__init__.py  (+1 lines)
  edited  frontend/messages/ja.json  (+11 lines)
  => 4 new files, 2 registrations, 191 non-blank lines generated

Next: add this one line under `nodes:` in nodes.yaml
  robot.agv: [agv_1, agv_2]
```

Open `nodes.yaml` on screen and add the line under `nodes:`:

```yaml
  robot.agv: [agv_1, agv_2]
```

Refresh the browser. Show:

- Sidebar → ロボット → **AGV** (new entry).
- The AGV page lists `agv_1`, `agv_2` with state 待機 (waiting); they patrol near the map center on 地図 (map).
- 設定 (Config) → ロボット / AGV: instances and the generated `patrol_radius` field are editable in the UI —
  more AGVs are added by operators, not engineers.

Talking point: the generated node follows the existing `abstract.Node` → `robot.Node` pattern (same as
`backend/src/robot/dummy`), so it gets status reporting, map display, job assignment and config forms for free.
The only part left for an engineer is the `TODO` in `node.py::_poll()` that talks to the real AGV controller.

## Beat 2 — new automation block for on-site staff

> "Now the plant wants AGVs to run an inspection step. Instead of a change request to engineering,
> we publish a block that shift leads drag into a job."

```bash
python3 scripts/create_task_block.py robot.agv inspect --label 点検
```

```
create-task-block robot.agv.inspect
  created backend/src/job/task/robot/agv/inspect/__init__.py  (4 lines)
  created backend/src/job/task/robot/agv/inspect/domain.py  (87 lines)
  created backend/src/job/task/robot/agv/inspect/logic.py  (27 lines)
  edited  backend/src/job/task/robot/agv/__init__.py  (+1 lines)
  edited  backend/src/job/task/robot/__init__.py  (+1 lines)
  => 3 new files, 2 registrations, 120 non-blank lines generated
```

Open ジョブ作成 (Job Creator) and refresh. Click the **AGV** toolbox category (node `robot.agv`, shown with the
label `create-node` wrote) → the **点検** block is there, with a robot socket and a duration (seconds) socket. Drag it in, plug in a robot variable, save.

Talking point: `domain.py` implements `define_block()` / `define_toolbox()` exactly like
`backend/src/job/task/common/control/controls_select/domain.py`; `JobCreate.fetch_define()` discovers it at
runtime, so **no frontend change and no frontend rebuild**.

## Beat 3 — one-command site spin-up + traces

> "Every plant gets the same stack, the same way."

```bash
docker compose down -v      # wipe everything (database included)
docker compose up -d        # one command; ~30 s with pre-pulled images
docker compose ps           # db healthy, backend healthy, frontend up
```

Log in again (`admin` / `admin123` is re-seeded automatically) — the AGVs are still there because they are
defined in `nodes.yaml`, which is the site's configuration under version control.

Traces for triage:

- UI → 実行ログ (Log): structured, per-node logs stored in PostgreSQL (`freedom_log_*` partitions). Rows with
  name `src.robot.agv` show `[agv_1] launch ...`; running a job with the 点検 block adds
  `start: 点検 robot=agv_1 ...` / `finish: ...` rows.
- Terminal: `docker compose logs -f backend` shows the same lines plus each hot-reload
  (`changes detected` → `update node='robot.agv' ...`).

Talking point: when a site reports a problem, the engineer starts from a reproducible stack and a per-node trace
instead of a hand-built server.

## Value table

Numbers are the generators' own output (non-blank lines; re-check any time with `--dry-run`, which prints the
same summary without writing). "By hand" is what an engineer writes today to get the same result.

| | Files created | Registrations edited | Lines generated | Human input with generator | By hand today |
|---|---|---|---|---|---|
| `create-node robot agv` | 4 | 2 (+ `nodes.yaml`) | 191 (+1 YAML line) | 1 command + 1 YAML line | 4 files + 3 registrations (Python package import, `config/*.py` structure + seed, `ja.json` label) ≈ 192 lines |
| `create-task-block robot.agv inspect` | 3 | 2 | 120 | 1 command | 3 files + 2 package imports ≈ 120 lines |
| `docker compose up` | — | — | — | 1 command | `docs/install.md`: install Python 3.13, venv + pip, Node 24, PostgreSQL 16, create DB/schema, write `.env`, Better Auth migration, seed admin, start 2 processes |

For reference, the hand-written equivalents already in the repo: `backend/src/robot/dummy/` is 4 files / 134
lines (plus 5 seed lines and 1 structure line in `backend/config/dummy.py`); the
`controls_select` block is 3 files / 133 lines.

## Live demo safety

### Pre-built images

```bash
docker compose pull                        # ghcr.io/akahn23/freedom-{backend,frontend}:latest + postgres:16-alpine
FREEDOM_TAG=<tag> docker compose pull      # pin a specific build
```

If the images are not published (or you are offline), build them once while you still have network:
`docker compose build` (~3 min). After that `docker compose up` needs no network at all.

### Verification checklist (do this the day before AND 30 min before the meeting)

- [ ] `git status` is clean, or run `scripts/demo_reset.sh` to remove a previous rehearsal's `robot.agv`.
- [ ] `docker compose down -v && docker compose up -d` → `docker compose ps` shows db/backend healthy, frontend up.
- [ ] http://localhost:3000 → login `admin` / `admin123` works.
- [ ] Dashboard shows ロボット → ダミー with 3 robots; 地図 (map) renders.
- [ ] Full rehearsal of beats 1–2 (AGV appears, 点検 block appears), then `scripts/demo_reset.sh`
      and refresh the browser (AGV gone again).
- [ ] Laptop: Docker Desktop running, ≥ 4 GB free memory, ports 3000/8080/5432-in-container free,
      notifications off, browser zoom 100 %, terminal font large.
- [ ] Screen recording of the full run is on the desktop (see below).

### Fallback

Record the whole runbook once when it works (`docker compose down -v` → beats 1–3) at 1080p. If anything fails
live — Docker won't start, network/VPN blocks localhost, login fails — **don't debug in front of the CIO**:
say "let me show you the recording from this morning" and play it, then offer a follow-up session. Keep the
recording offline (local file, not a streaming link).

### Reset between rehearsals

```bash
scripts/demo_reset.sh      # removes generated robot.agv files and restores nodes.yaml / ja.json / __init__.py
```

The AGV rows stay in the database config table but are ignored once `robot.agv` is removed from `nodes.yaml`;
`docker compose down -v` gives a completely fresh database.
