# Bookmark attachments — design

## Goal

Download each bookmarked toot's media attachments into a configured folder,
and embed them in the toot's markdown file using Obsidian syntax.

## Configuration

A new key in `config.toml`:

```toml
attachments_dir = "bookmarks/attachments"
```

`config.example.toml` gains this line with that value.

## Filenames

`<status id>-<attachment id><ext>`, e.g. `112233-998877.png`.

- Attachment ids are unique per instance, so names don't clash.
- `<ext>` is the suffix of the path of the attachment's `url`, including the
  dot (e.g. `.png`). If the path has no suffix, the filename has none.

A helper `attachment_filename(status_id: str, attachment: dict) -> str`
builds this name. Both the markdown and the downloader use it.

## Markdown

After the body text, each attachment with a `url` gets one line
`![[<filename>]]`, separated by blank lines. The filename has no directory.
Obsidian uses the same syntax for images, video and audio, so all types are
treated alike. Attachment descriptions are not written out.

```
---
author: "@alice@example.social"
date: 2026-10-30T14:02:00Z
url: https://example.social/@alice/112233
---

Look at this cat!

![[112233-998877.png]]

![[112233-998878.mp4]]
```

A toot with no attachments, or whose attachments all lack a `url`, renders
exactly as before. The file still ends with a single trailing newline.

## Downloading

`save_attachments(statuses: list[dict], attachments_dir) -> None`:

- Creates `attachments_dir` (with parents) if needed.
- For each status, for each item in `status["media_attachments"]`:
  - Skip it if `url` is missing or null.
  - Skip it if the target file already exists.
  - Otherwise, `requests.get(url)` without any `Authorization` header (media
    is public, and the token must not be sent to media hosts), call
    `raise_for_status()`, and write `response.content` to the file.
  - If the request fails (`requests.RequestException`), log a warning with the
    URL and error, and move on to the next attachment.

`main` calls `save_attachments(statuses, config["attachments_dir"])` before
`save_bookmarks`, so a missing config key stops the script before any markdown
is written.

## Error handling

A failed attachment download is logged and skipped (real instances return
500s for some remote media via `/media_proxy/`). The toot's embed is still
written, so it points at a missing file until a later run succeeds. Other
errors stop the script as before.

## Testing

In `test_bookmarks.py`:

- `attachment_filename`: builds `<status id>-<attachment id><ext>` from the
  URL; works when the URL has no suffix.
- `status_to_markdown`: one attachment, two attachments in order, and an
  attachment without a `url` is skipped. The existing no-attachment test
  still passes, with `"media_attachments": []` added to its status.
- `save_attachments`, with `requests.get` faked as in the fetch tests:
  writes the downloaded bytes to the right filename in a new directory, skips
  an existing file without calling `get`, skips attachments without a `url`,
  sends no `Authorization` header, and on an HTTP error logs a warning and
  carries on with the next attachment.

Real Mastodon statuses always include `media_attachments` (possibly empty),
so the code may read `status["media_attachments"]` directly. Existing test
status dicts gain `"media_attachments": []`.

## README

Document `attachments_dir` in the configure section, and mention that
attachments are downloaded and embedded.

## Out of scope

Alt text, thumbnails/previews, remote_url fallback, re-downloading changed
media, cleaning up orphaned attachments.
