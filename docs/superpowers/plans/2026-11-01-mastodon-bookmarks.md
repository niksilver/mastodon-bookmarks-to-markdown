# Mastodon Bookmarks to Markdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** A really simple script that fetches all Mastodon bookmarks for one account and writes each to its own markdown file with YAML front matter.

**Architecture:** One module, `bookmarks.py`, of small functions (config loading, fetching with pagination, HTML-to-text, markdown rendering, saving), wired together by `main()`. Tests live in `test_bookmarks.py` and mock `requests.get` for network calls.

**Tech Stack:** Python 3.11+ (for `tomllib`), uv, requests, pytest.

**Spec:** `docs/superpowers/specs/2026-11-01-mastodon-bookmarks-design.md`

**Git:** Do NOT commit. The user makes all commits themselves.

**Status:**: Done

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock` | Created by uv; dependencies |
| `.gitignore` | Ignore `config.toml`, `bookmarks/`, `.venv/`, `__pycache__/`, `.pytest_cache/` |
| `config.example.toml` | Placeholder config to copy |
| `bookmarks.py` | All script logic |
| `test_bookmarks.py` | All unit tests |

Before writing code, load the codebase style skills: `python-imports`,
`python-docstrings`, `python-assignments`, `python-line-spacing`,
`python-parameters`, and follow `test-driven-development`.

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`, `uv.lock` (via uv), `.gitignore`, `config.example.toml`

**Status:**: Done

- [x] **Step 1: Initialise with uv**

Run: `uv init --bare --name mastodon-bookmarks-to-markdown`
(`--bare` creates only `pyproject.toml`: no sample `main.py`, no README, and no git init.)
Confirm `requires-python` in `pyproject.toml` is `>=3.11`, and edit it if it isn't.

- [x] **Step 2: Add dependencies**

Run: `uv add requests` then `uv add --dev pytest`
Expected: `pyproject.toml` lists `requests` in dependencies and `pytest` in the `dev` dependency group, and `uv.lock` exists.

- [x] **Step 3: Create `.gitignore`**

Lines: `config.toml`, `bookmarks/`, `.venv/`, `__pycache__/`, `.pytest_cache/`.

- [x] **Step 4: Create `config.example.toml`**

```toml
instance_url = "https://example.social"
access_token = "your-token-with-read:bookmarks-scope"
output_dir   = "bookmarks"
```

- [x] **Step 5: Verify pytest runs**

Run: `uv run pytest`
Expected: "no tests ran" (exit code 5). That's fine at this stage.

---

### Task 2: `load_config`

**Files:**
- Create: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Done

- [x] **Step 1: Write the failing test**

`test_load_config`: write a small TOML string (all three keys) to
`tmp_path / "config.toml"`, call `load_config(path)`, and assert the result
equals the expected dict.

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest test_bookmarks.py::test_load_config -v`
Expected: FAIL (ImportError: `load_config` not defined).

- [x] **Step 3: Implement**

  - [x] `load_config(path) -> dict`
  - [x] Open the file in binary mode (`"rb"`, which `tomllib` requires) and return `tomllib.load(f)`.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest test_bookmarks.py::test_load_config -v`
Expected: PASS

---

### Task 3: `html_to_text`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Done

- [x] **Step 1: Write the failing tests**

One small test per behaviour:
- `test_html_to_text_single_paragraph`: `"<p>Hello</p>"` → `"Hello"`
- `test_html_to_text_paragraphs`: `"<p>One</p><p>Two</p>"` → `"One\n\nTwo"`
- `test_html_to_text_line_breaks`: `"<p>One<br>Two<br />Three</p>"` → `"One\nTwo\nThree"`
- `test_html_to_text_strips_tags`: `'<p>See <a href="https://x.y"><span>x.y</span></a></p>'` → `"See x.y"`
- `test_html_to_text_unescapes_entities`: `"<p>A &amp; B &lt;3</p>"` → `"A & B <3"`

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_bookmarks.py -k html_to_text -v`
Expected: FAIL (ImportError).

- [x] **Step 3: Implement**

  - [x] `html_to_text(html: str) -> str`
  - [x] Use `re.sub` to replace `<br>` variants (`<br\s*/?>`) with `"\n"`.
  - [x] Replace `</p>\s*<p>` with `"\n\n"`.
  - [x] Strip any remaining tags with `<[^>]+>`.
  - [x] Unescape with `html.unescape` and return the `.strip()`ped result.
  - Note: entities must be unescaped *after* the tags are stripped. Otherwise `&lt;3` would turn into `<3` and could be mistaken for a tag.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_bookmarks.py -k html_to_text -v`
Expected: 5 PASS

---

### Task 4: `status_to_markdown`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Done

- [x] **Step 1: Write the failing test**

`test_status_to_markdown`: build a minimal status dict:

```python
status = {
    "id":         "112233",
    "created_at": "2026-10-30T14:02:00Z",
    "url":        "https://example.social/@alice/112233",
    "account":    {"acct": "alice@example.social"},
    "content":    "<p>Hello &amp; welcome</p>",
}
```

Assert the result equals exactly:

```
---
author: "@alice@example.social"
date: 2026-10-30T14:02:00Z
url: https://example.social/@alice/112233
---

Hello & welcome
```

including one trailing newline at the end.

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest test_bookmarks.py::test_status_to_markdown -v`
Expected: FAIL (ImportError).

- [x] **Step 3: Implement**

  - [x] `status_to_markdown(status: dict) -> str`
  - [x] Build the string from the front matter lines, a blank line, `html_to_text(status["content"])` and a trailing newline. The author is `"@" + status["account"]["acct"]`, wrapped in double quotes because YAML would treat a leading `@` as reserved.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest test_bookmarks.py::test_status_to_markdown -v`
Expected: PASS

---

### Task 5: `save_bookmarks`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Done

- [x] **Step 1: Write the failing tests**

- `test_save_bookmarks_writes_one_file_per_status`: two status dicts (ids
  `"1"` and `"2"`, otherwise shaped like the one in Task 4). Output dir is
  `tmp_path / "out"`, which doesn't exist yet. Assert `out/1.md` and `out/2.md`
  both exist and that each file's contents equal `status_to_markdown(status)`.
- `test_save_bookmarks_overwrites_existing`: create `out/1.md` with the text
  `"old"`, save status id `"1"`, and assert the contents have been replaced.

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_bookmarks.py -k save_bookmarks -v`
Expected: FAIL (ImportError).

- [x] **Step 3: Implement**

  - [x] `save_bookmarks(statuses: list[dict], output_dir) -> None`
  - [x] `Path(output_dir).mkdir(parents=True, exist_ok=True)`
  - [x] For each status, call `(dir / f"{status['id']}.md").write_text(status_to_markdown(status), encoding="utf-8")`

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_bookmarks.py -k save_bookmarks -v`
Expected: 2 PASS

---

### Task 6: `fetch_bookmarks`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Done

Background: `GET {instance_url}/api/v1/bookmarks` returns a JSON list of
statuses. When there are more pages, the response has a `Link` header with a
`rel="next"` URL. `requests` parses this header into `response.links`, which
looks like `{"next": {"url": "..."}}`. On the last page there is no `"next"` key.

**Mocking approach:** use pytest's `monkeypatch` to replace
`bookmarks.requests.get` with a fake. The fake records each call's URL and
headers and returns `FakeResponse` objects from a queue. `FakeResponse` is a
small class in the test file with a `json()` method, a `links` dict and a
no-op `raise_for_status()`. Don't use a mocking library.

- [x] **Step 1: Write the failing tests**

- `test_fetch_bookmarks_sends_token_and_returns_statuses`: one page with two
  statuses and empty `links`. Assert that the result is both statuses, that
  the URL called was `"https://example.social/api/v1/bookmarks"`, and that the
  headers included `{"Authorization": "Bearer tok"}`.
- `test_fetch_bookmarks_follows_next_link`: page 1 has `links={"next": {"url":
  "https://example.social/api/v1/bookmarks?max_id=5"}}` and page 2 has empty
  links. Assert that the result contains page 1's statuses followed by page 2's,
  that the second call went to the `next` URL, and that it also carried the token.
- `test_fetch_bookmarks_raises_on_http_error`: give `FakeResponse` an optional
  error to raise from `raise_for_status()`. Pass it
  `requests.HTTPError("401")` and assert that `fetch_bookmarks` raises
  `requests.HTTPError`.

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest test_bookmarks.py -k fetch_bookmarks -v`
Expected: FAIL (ImportError).

- [x] **Step 3: Implement**

  - [x] `fetch_bookmarks(instance_url: str, token: str) -> list[dict]`
  - [x] Build `headers = {"Authorization": f"Bearer {token}"}` and set the starting URL to `instance_url.rstrip("/") + "/api/v1/bookmarks"`.
  - [x] Loop while there is a URL: `requests.get(url, headers=headers)`, then `raise_for_status()`, then extend the results with `response.json()`, then set `url = response.links.get("next", {}).get("url")`.
  - [x] Return the results.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest test_bookmarks.py -k fetch_bookmarks -v`
Expected: 3 PASS

---

### Task 7: `main` and final check

**Files:**
- Modify: `bookmarks.py`

**Status:**: Done

`main` is just glue code, so per the spec it has no unit test of its own.

- [x] **Step 1: Implement**

  - [x] `main() -> None`: `config = load_config("config.toml")`, then call `fetch_bookmarks(config["instance_url"], config["access_token"])`, pass the result to `save_bookmarks(statuses, config["output_dir"])`, and print how many files were written.
  - [x] Add `if __name__ == "__main__": main()` at the bottom of the file.

- [x] **Step 2: Run the full suite**

Run: `uv run pytest -v`
Expected: all 12 tests pass.

- [x] **Step 3: Smoke test (manual, by the user)**

Copy `config.example.toml` to `config.toml`, fill in the real values, then run
`uv run python bookmarks.py`. Expected: `bookmarks/<id>.md` files appear.

- [x] **Step 4: Hand over to the user**

Tell the user which files are ready. Do not commit anything.
