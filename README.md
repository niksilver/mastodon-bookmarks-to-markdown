# Mastodon bookmarks to markdown

A small script that fetches all the bookmarks from your Mastodon account and
saves each one as its own markdown file, with YAML front matter for the author,
date and link.

## Configure

You need [uv](https://docs.astral.sh/uv/).

1. In Mastodon, go to Preferences → Development → New application and create
   an application with the `read:bookmarks` scope. Copy its access token.
2. Copy the example config and fill it in:

   ```sh
   cp config.example.toml config.toml
   ```

   ```toml
   instance_url = "https://your.instance"
   access_token = "your-access-token"
   output_dir   = "bookmarks"
   ```

`config.toml` is git-ignored, so your token won't be committed.

## Run

```sh
uv run python bookmarks.py
```

Each bookmark is written to `<output_dir>/<status id>.md`. Running it again
overwrites existing files.

## Test

```sh
uv run pytest
```
