# Maximum toot age — design

## Goal

Let the user export only bookmarked toots posted within the last N days.

## Configuration

An optional key in `config.toml`:

```toml
toot_max_days_ago = 0
```

`0`, or a missing key, means all bookmarks. `config.example.toml` includes it
with value `0` and a short comment.

## Behaviour

- Age is measured from each status's `created_at`. The Mastodon API does not
  expose when a status was bookmarked. The user chose this over tracking
  first-seen dates locally.
- Bookmarks are returned in bookmark order, not posting order, so all pages
  are still fetched; filtering happens afterwards.
- `filter_recent(statuses, toot_max_days_ago, now) -> list[dict]` returns the
  statuses with `created_at >= now - toot_max_days_ago days`, in their original
  order; with `toot_max_days_ago == 0` it returns them all. `now` is passed in
  (timezone-aware) so the function is testable.
- `main` calls it after fetching, logs `Keeping X of Y bookmarks`, and passes
  only the kept statuses to `save_attachments` and `save_bookmarks`.

## Testing

`filter_recent`: 0 keeps an old status; 7 keeps a 2-day-old status and drops
a month-old one.

## Out of scope

Stopping pagination early, deleting previously exported files that are now
too old.
