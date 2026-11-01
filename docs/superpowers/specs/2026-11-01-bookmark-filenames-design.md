# Bookmark filenames — design

## Goal

Name each toot's markdown file `YYYYMMDD-TEXT-ID.md` instead of `ID.md`.

## Format

- `YYYYMMDD`: the date part of the status's `created_at` (UTC), without dashes.
- `TEXT`: the first 12 characters of `html_to_text(status["content"])`, with
  every character other than ASCII `A-Z`, `a-z` and `0-9` replaced by `_`.
  Shorter text is used in full; a toot with no text gives an empty TEXT
  (e.g. `20261030--112233.md`).
- `ID`: the status id.

Example: `<p>Hello &amp; welcome</p>` posted 2026-10-30 with id 112233 gives
`20261030-Hello___welc-112233.md`.

## Code

`bookmark_filename(status: dict) -> str` builds the name; `save_bookmarks`
uses it. Attachment filenames are unchanged.

## Testing

`bookmark_filename`: normal text, short text, non-ASCII letters, no text.
The `save_bookmarks` tests expect the new names.

## Out of scope

Renaming or deleting files saved under the old `ID.md` names.
