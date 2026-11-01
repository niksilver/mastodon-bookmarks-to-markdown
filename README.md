# Mastodon bookmarks to markdown

A small script that fetches all the bookmarks from your Mastodon account and
saves each one as its own markdown file, with YAML front matter for the author,
date and link. Media attachments are downloaded and embedded Obsidian-style
(`![[file]]`).

## Configure

You need [uv](https://docs.astral.sh/uv/).

1. In Mastodon, go to Preferences → Development → New application and create
   an application with the `read:bookmarks` scope. Copy its access token.
2. Copy the example config and fill it in:

   ```sh
   cp config.example.toml config.toml
   ```

   ```toml
   instance_url      = "https://your.instance"
   access_token      = "your-access-token"
   output_dir        = "bookmarks"
   attachments_dir   = "bookmarks/attachments"
   toot_max_days_ago = 0
   ```

`toot_max_days_ago` limits the export to toots posted within that many days.
`0`, or leaving it out, means all bookmarks. It goes by when each toot was
posted, not when you bookmarked it, because Mastodon doesn't record bookmark
dates. All bookmarks are still fetched before filtering.

`config.toml` is git-ignored, so your token won't be committed.

## Run

```sh
uv run python bookmarks.py
```

Each bookmark is written to `<output_dir>/YYYYMMDD-TEXT-ID.md`, where the date
is when the toot was posted (UTC), TEXT is the first 12 characters of the toot
with anything other than ASCII letters and digits turned into `_`, and ID is the
toot's id. For example, `20261030-Hello___welc-112233.md`. Running it again
overwrites existing files.

Attachments are saved to `<attachments_dir>/<status id>-<attachment id>.<ext>`.
Attachments that have already been downloaded are skipped. If an attachment
fails to download, a warning is logged and the script carries on; run it again
later to retry.

## Test

```sh
uv run pytest
```
