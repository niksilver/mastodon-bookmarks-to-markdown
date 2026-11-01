# Bookmark Attachments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Download each bookmarked toot's media attachments into a configured folder and embed them in the toot's markdown with Obsidian `![[filename]]` syntax.

**Architecture:** Three additions to `bookmarks.py`: a filename helper (`attachment_filename`) shared by the markdown renderer and the downloader, embed lines added to `status_to_markdown`, and a new `save_attachments` called from `main`. Tests extend the existing hand-written `requests.get` fake.

**Tech Stack:** Python 3.11+, uv, requests, pytest.

**Spec:** `docs/superpowers/specs/2026-11-01-attachments-design.md`

**Git:** Do NOT commit. The user makes all commits themselves.

**Status:**: Not started

---

## Existing code to know about

- `bookmarks.py`: `load_config`, `html_to_text(content)`, `status_to_markdown(status)`, `save_bookmarks(statuses, output_dir)`, `fetch_bookmarks(instance_url, token)` and `main()`. It imports `html`, `pathlib`, `re`, `tomllib` and `requests`.
- `test_bookmarks.py`:
  - `_make_status(status_id)` builds a status dict.
  - `test_status_to_markdown` builds its own status dict.
  - `FakeResponse(statuses, links = None, error = None)` has `json()`, `links` and `raise_for_status()`.
  - `_install_fake_get(monkeypatch, responses)` patches `bookmarks.requests.get` with `fake_get(url, headers)`. It records `(url, headers)` tuples and returns the list of calls.
- Conventions:
  - Tests use `import bookmarks`.
  - Imports are module-style only. For example, `import urllib.parse` and then `urllib.parse.urlparse(...)`.
  - Docstrings are markdown, with `## Parameters` and `## Returns` sections. Test docstrings include `## Returns` / `None`.
  - Consecutive assignments and dict values have aligned `=` signs and values.
  - Keyword arguments have spaces around `=`, e.g. `encoding = "utf-8"`.
  - Before writing code, load the skills `test-driven-development`, `python-imports`, `python-docstrings`, `python-assignments`, `python-line-spacing` and `python-parameters`.

Run tests with `uv run pytest` (never pip). There are 12 tests at the start.

## File structure

| File | Change |
|---|---|
| `bookmarks.py` | Add `attachment_filename` and `save_attachments`; change `status_to_markdown` and `main` |
| `test_bookmarks.py` | Add `media_attachments` to test statuses, extend the fakes, and add 10 tests |
| `config.example.toml` | Add `attachments_dir` |
| `README.md` | Document `attachments_dir` and attachments |

---

### Task 1: Config and test data

**Files:**
- Modify: `config.example.toml`, `test_bookmarks.py`

**Status:**: Not started

- [ ] **Step 1:** Add `attachments_dir = "bookmarks/attachments"` to `config.example.toml`, with its `=` aligned to the other keys.
- [ ] **Step 2:** Add `"media_attachments": []` to the dict returned by `_make_status` and to the `status` dict in `test_status_to_markdown`. Keep the values aligned.
- [ ] **Step 3:** Run `uv run pytest`. Expected: 12 pass. There's no behaviour change yet.

---

### Task 2: `attachment_filename`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Not started

- [ ] **Step 1: Write failing tests**
  - `test_attachment_filename_uses_ids_and_extension`: `bookmarks.attachment_filename("112233", {"id": "998877", "url": "https://files.example.social/media/abc/original/f00.png"})` → `"112233-998877.png"`
  - `test_attachment_filename_without_extension`: a URL whose path has no suffix, e.g. `https://files.example.social/media/abc`, gives `"112233-998877"`.
- [ ] **Step 2:** Run `uv run pytest -k attachment_filename -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `attachment_filename(status_id: str, attachment: dict) -> str`
  - Get the extension with `pathlib.PurePosixPath(urllib.parse.urlparse(attachment["url"]).path).suffix`. This includes the dot and is `""` if there is no suffix. Parsing the URL first means a query string can't end up in the extension.
  - Return `f"{status_id}-{attachment['id']}{suffix}"`.
  - Add `import urllib.parse` to the stdlib import block, in alphabetical order.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: 14 pass.

---

### Task 3: Embeds in `status_to_markdown`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Not started

- [ ] **Step 1: Write failing tests**, using `_make_status("112233")` and setting `media_attachments`. Each test asserts the exact full string, written in the same parenthesised one-line-per-output-line style as `test_status_to_markdown`.
  - `test_status_to_markdown_embeds_attachment`: one attachment `{"id": "1", "url": ".../a.png"}`. The body ends `...Hello & welcome\n\n![[112233-1.png]]\n`.
  - `test_status_to_markdown_embeds_attachments_in_order`: attachments `a.png` (id 1) and `b.mp4` (id 2). The body ends `Hello & welcome\n\n![[112233-1.png]]\n\n![[112233-2.mp4]]\n`.
  - `test_status_to_markdown_skips_attachment_without_url`: one attachment `{"id": "1", "url": None}`. The output equals the output with no attachments, i.e. it ends `Hello & welcome\n`.
- [ ] **Step 2:** Run `uv run pytest -k status_to_markdown -v`. Expected: the 3 new tests FAIL and the old one passes.
- [ ] **Step 3: Implement**
  - Build the body as a list of blocks. Start with the text, then add `f"![[{attachment_filename(status['id'], a)}]]"` for each attachment in `status["media_attachments"]` that has a URL (`a.get("url")`).
  - Join the blocks with `"\n\n"`, and keep the front matter and the single trailing newline as they are now.
  - Update the docstring: `status` keys now include `id` and `media_attachments`.
- [ ] **Step 4:** Run `uv run pytest -v`. Expected: 17 pass.

---

### Task 4: `save_attachments`

**Files:**
- Modify: `bookmarks.py`, `test_bookmarks.py`

**Status:**: Not started

- [ ] **Step 1: Extend the test fakes**
  - `FakeResponse.__init__` gets an extra `content = b""` parameter, stored as `self.content` and documented in the docstring. Existing calls still work.
  - `fake_get` in `_install_fake_get` becomes `fake_get(url, headers = None)`, so that it accepts calls without headers. It still records `(url, headers)`.
- [ ] **Step 2: Write failing tests**. Each uses `tmp_path / "att"` as the directory, which doesn't exist yet, and a status from `_make_status("112233")` with `media_attachments` set.
  - `test_save_attachments_writes_file`: one attachment `{"id": "1", "url": "https://files.example.social/a.png"}`, and a fake response with `content = b"PNG"`. Assert that `att/112233-1.png` has bytes `b"PNG"` and that one call was made to that URL.
  - `test_save_attachments_sends_no_auth_header`: same setup. Assert the recorded headers are `None`.
  - `test_save_attachments_skips_existing_file`: create `att/112233-1.png` containing `b"old"`, then call with no queued responses. Assert there were no calls and the file still contains `b"old"`.
  - `test_save_attachments_skips_attachment_without_url`: an attachment with `"url": None`. Assert there were no calls.
  - `test_save_attachments_raises_on_http_error`: the response has `error = requests.HTTPError("404")`. Assert `pytest.raises(requests.HTTPError)`.
- [ ] **Step 3:** Run `uv run pytest -k save_attachments -v`. Expected: FAIL.
- [ ] **Step 4: Implement** `save_attachments(statuses: list[dict], attachments_dir) -> None`
  - `pathlib.Path(attachments_dir).mkdir(parents = True, exist_ok = True)`
  - For each status, for each attachment in `status["media_attachments"]`:
    - `continue` if there's no `attachment.get("url")`.
    - Set `path = directory / attachment_filename(status["id"], attachment)`, and `continue` if `path.exists()`.
    - Call `response = requests.get(attachment["url"])`. Don't pass headers, because the token must never go to media hosts.
    - Call `response.raise_for_status()`, then `path.write_bytes(response.content)`.
  - Put it after `save_bookmarks` in the file.
- [ ] **Step 5:** Run `uv run pytest -v`. Expected: 22 pass.

---

### Task 5: Wire into `main` and update the README

**Files:**
- Modify: `bookmarks.py`, `README.md`

**Status:**: Not started

`main` is glue code with no unit test, the same as before.

- [ ] **Step 1:** In `main`, after `save_bookmarks(...)`, call `save_attachments(statuses, config["attachments_dir"])`. Update its docstring to mention attachments.
- [ ] **Step 2: README**
  - Mention in the opening description that media attachments are downloaded and embedded Obsidian-style (`![[file]]`).
  - Add the `attachments_dir = "bookmarks/attachments"` line to the config example.
  - In "Run", say that attachments go to `<attachments_dir>/<status id>-<attachment id>.<ext>` and that existing attachment files are skipped.
- [ ] **Step 3:** Run `uv run pytest -v`. Expected: 22 pass. Then run `uv run python -c "import bookmarks"` and confirm it produces no output.
- [ ] **Step 4:** Hand over to the user. Do not commit.
