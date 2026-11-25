---
name: pr-review
description: Review a pull request or the current branch's changes against this habit-tracker repo's conventions, run the full verification suite, and report findings by severity. Use when asked to review a PR, a branch, or "my changes" in this repo.
---

# PR review (habit-tracker)

Review changes for correctness and for this repo's conventions (see `CLAUDE.md`). Never edit files, commit, or push. Locally, **report only** — don't post comments on GitHub unless the user asks. In GitHub Actions, follow "Running in CI" at the end instead.

## 1. Get the diff

Pick the target from the user's request:

- PR number given: `gh pr view <n>` for title/description, then `gh pr diff <n>`. To run checks, check out the PR with `gh pr checkout <n>` only if the working tree is clean, and tell the user you switched branches.
- Otherwise, the current branch: `git diff main...HEAD` plus `git diff HEAD` for uncommitted changes.

If the diff is empty, say so and stop.

Read every changed file in full, not just the hunks, where the surrounding code matters.

## 2. Check against the repo's rules

**Scope and dependencies**
- No new dependencies in `backend/pyproject.toml` or `frontend/package.json` unless the PR says why. Flag any lockfile change (`uv.lock`, `package-lock.json`) that doesn't match a manifest change.
- No features beyond what the PR describes.
- No committed `habits.db`, `.venv`, `node_modules`, `dist`, or `__pycache__`.

**Backend (`backend/src/backend/`)**
- New routes go on the `/api` router, not directly on `app`.
- Handlers take the DB via `SessionDep`; missing rows return 404 via `HTTPException`.
- Request bodies use a separate input model (like `HabitCreate`) with validation; responses use a read model (like `HabitRead`).
- Use `session.exec(select(...))`, not `session.query(...)`.
- Model or table changes: call out that there are no migrations and existing `habits.db` files must be deleted.
- Date logic: "today" is `date.today()` on the server; flag anything that mixes this with client dates or UTC datetimes inconsistently.

**Backend tests (`backend/tests/`)**
- Every new or changed endpoint has a test, including its error cases.
- Tests use the in-memory `session` and `client` fixtures; `TestClient(app)` is never used in a `with` block (that would create `habits.db`).

**Frontend (`frontend/src/`)**
- API calls use relative `/api/...` URLs (the Vite proxy handles the host).
- Failed requests are surfaced to the user, not swallowed.
- Types match the backend's response shape (e.g. `done_today`).
- New behavior is covered in a component test that mocks `fetch` with `vi.stubGlobal` and imports test APIs from `vitest`.

## 3. Run the checks

Run each command separately (PowerShell 5.1 has no `&&`) and keep the output:

In `backend/`:
- `uv run ruff check .`
- `uv run pytest`

In `frontend/`:
- `npm run lint`
- `npm test -- --run`
- `npm run build`

A failing check is a finding. Don't fix it.

## 4. Report

Start with a one-line verdict: **ready to merge**, **needs changes**, or **blocked** (checks failing).

Then a table of check results (command → pass/fail, with the failure summary).

Then findings, most severe first, each with:
- severity: **bug** (wrong behavior), **convention** (breaks a rule above), or **nit**
- location as a clickable `path:line` link
- what's wrong and a concrete failure scenario for bugs
- the suggested fix in a sentence or a short snippet

Only report findings you've confirmed by reading the code. If there are none, say so plainly. End with anything you couldn't verify (for example, behavior that needs the app running in a browser).

## Running in CI

When the prompt gives a PR number and says you're in GitHub Actions (`.github/workflows/claude-pr-review.yml`), these rules replace the local ones above:

- **Environment:** Linux bash, repo root as working directory, PR branch already checked out with dependencies installed. Don't run `gh pr checkout`, `uv sync` or `npm ci`. Only one commit is fetched, so `git diff main...HEAD` won't work.
- **Diff:** `gh pr view <n>` and `gh pr diff <n>`. Read changed files from the working tree.
- **Checks:** run exactly these, from the repo root (only these forms are allowed):
  - `uv run --directory backend ruff check .`
  - `uv run --directory backend pytest`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend test -- --run`
  - `npm --prefix frontend run build`
- **Inline comments:** one per finding that points at a changed line, using `mcp__github_inline_comment__create_inline_comment` with `confirmed: true`. Put the severity first (`**bug:**`, `**convention:**`, `**nit:**`), then the problem and the fix. Skip findings on lines outside the diff; they go in the summary instead.
- **Summary comment:** post exactly one with `gh pr comment <n> --body-file -` (pipe the body in via a heredoc). It contains the verdict, the check-results table, and a one-line list of findings (or "No issues found."). End with `_Automated review by Claude using .claude/skills/pr-review._`
- **Output:** all feedback goes in GitHub comments; don't put review text only in your final message.
