# Mastodon bookmarks to markdown — design

## Goal

A really simple Python script that fetches all bookmarks from one Mastodon
account and saves each bookmark as its own markdown file.

## Tooling

- Managed with uv (not pip): `uv init`, `uv add requests`, `uv add --dev pytest`.
- Run: `uv run python bookmarks.py`
- Test: `uv run pytest`

## Configuration

A `config.toml` file in the working directory, read with the standard
library `tomllib`:

```toml
instance_url = "https://example.social"
access_token = "..."          # token with read:bookmarks scope
output_dir   = "bookmarks"
```

`config.toml` is git-ignored. A `config.example.toml` with placeholder values
is committed.

## Code structure

A single module, `bookmarks.py`, made of small functions:

- `load_config(path)` — reads the TOML file and returns a dict.
- `fetch_bookmarks(instance_url, token)` — GETs `/api/v1/bookmarks` with a
  bearer token, follows the `Link` header's `rel="next"` URL until there is
  none, and returns a list of all status dicts.
- `html_to_text(html)` — converts `<br>` to a newline and `</p><p>` to a blank
  line, strips all remaining tags, unescapes HTML entities, and trims
  surrounding whitespace. Standard library only.
- `status_to_markdown(status)` — returns a string of YAML front matter
  followed by the body text:

  ```
  ---
  author: "@alice@example.social"
  date: 2026-10-30T14:02:00Z
  url: https://example.social/@alice/112233
  ---

  The post text goes here...
  ```

  `author` is `"@" + status["account"]["acct"]`, `date` is
  `status["created_at"]`, `url` is `status["url"]`, and the body is
  `html_to_text(status["content"])`.
- `save_bookmarks(statuses, output_dir)` — creates `output_dir` if needed and
  writes `<status id>.md` for each status, overwriting existing files.
- `main()` — loads `config.toml`, fetches, and saves.

## Error handling

None beyond `response.raise_for_status()`. Any failure stops the script with
a traceback.

## Testing

pytest, in `test_bookmarks.py`:

- `load_config` reads a TOML file written to `tmp_path`.
- `fetch_bookmarks` with `requests.get` mocked: sends the bearer token,
  returns a single page, and follows a `next` link across two pages.
- `html_to_text`: paragraphs, line breaks, tags (e.g. links) stripped,
  entities unescaped.
- `status_to_markdown` produces the exact expected string.
- `save_bookmarks` writes one correctly named file per status into
  `tmp_path`.

## Out of scope

Boosts/reblog unwrapping, media attachments, content warnings, incremental
sync, OAuth flows, and error handling beyond the above.
