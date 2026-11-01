import pytest
import requests

import bookmarks


def _make_status(status_id):
    """
    Build a test status dict with the given id.

    ## Parameters

    - `status_id`: The status id to use

    ## Returns

    A status dict with all required keys
    """
    return {
        "id":         status_id,
        "created_at": "2026-10-30T14:02:00Z",
        "url":        f"https://example.social/@alice/{status_id}",
        "account":    {"acct": "alice@example.social"},
        "content":    "<p>Hello &amp; welcome</p>",
    }


def test_load_config(tmp_path):
    """
    Test that load_config reads a TOML file and returns a dict.

    ## Parameters

    - `tmp_path`: pytest temporary directory fixture

    ## Returns

    None
    """
    config_content = """instance_url = "https://example.social"
access_token = "test-token"
output_dir   = "bookmarks"
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    result = bookmarks.load_config(config_file)

    expected = {
        "instance_url": "https://example.social",
        "access_token": "test-token",
        "output_dir":   "bookmarks",
    }
    assert result == expected


def test_html_to_text_single_paragraph():
    """
    Test that a single paragraph is converted to plain text.

    ## Returns

    None
    """
    result = bookmarks.html_to_text("<p>Hello</p>")
    assert result == "Hello"


def test_html_to_text_paragraphs():
    """
    Test that multiple paragraphs are separated by double newlines.

    ## Returns

    None
    """
    result = bookmarks.html_to_text("<p>One</p><p>Two</p>")
    assert result == "One\n\nTwo"


def test_html_to_text_line_breaks():
    """
    Test that <br> and <br /> tags are converted to single newlines.

    ## Returns

    None
    """
    result = bookmarks.html_to_text("<p>One<br>Two<br />Three</p>")
    assert result == "One\nTwo\nThree"


def test_html_to_text_strips_tags():
    """
    Test that HTML tags are stripped from the content.

    ## Returns

    None
    """
    html_in = '<p>See <a href="https://x.y"><span>x.y</span></a></p>'
    result  = bookmarks.html_to_text(html_in)
    assert result == "See x.y"


def test_html_to_text_unescapes_entities():
    """
    Test that HTML entities are unescaped.

    ## Returns

    None
    """
    result = bookmarks.html_to_text("<p>A &amp; B &lt;3</p>")
    assert result == "A & B <3"


def test_status_to_markdown():
    """
    Test that a Mastodon status is converted to markdown with YAML front matter.

    ## Returns

    None
    """
    status = {
        "id":         "112233",
        "created_at": "2026-10-30T14:02:00Z",
        "url":        "https://example.social/@alice/112233",
        "account":    {"acct": "alice@example.social"},
        "content":    "<p>Hello &amp; welcome</p>",
    }

    result = bookmarks.status_to_markdown(status)

    expected = ('---\n'
                'author: "@alice@example.social"\n'
                'date: 2026-10-30T14:02:00Z\n'
                'url: https://example.social/@alice/112233\n'
                '---\n'
                '\n'
                'Hello & welcome\n'
                )
    assert result == expected


def test_save_bookmarks_writes_one_file_per_status(tmp_path):
    """
    Test that save_bookmarks writes one markdown file per status.

    ## Parameters

    - `tmp_path`: pytest temporary directory fixture

    ## Returns

    None
    """
    status1    = _make_status("1")
    status2    = _make_status("2")
    output_dir = tmp_path / "out"

    bookmarks.save_bookmarks([status1, status2], output_dir)

    assert (output_dir / "1.md").exists()
    assert (output_dir / "2.md").exists()
    expected1 = bookmarks.status_to_markdown(status1)
    expected2 = bookmarks.status_to_markdown(status2)
    assert (output_dir / "1.md").read_text(encoding = "utf-8") == expected1
    assert (output_dir / "2.md").read_text(encoding = "utf-8") == expected2


def test_save_bookmarks_overwrites_existing(tmp_path):
    """
    Test that save_bookmarks overwrites existing files.

    ## Parameters

    - `tmp_path`: pytest temporary directory fixture

    ## Returns

    None
    """
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "1.md").write_text("old")

    status = _make_status("1")
    bookmarks.save_bookmarks([status], output_dir)

    expected = bookmarks.status_to_markdown(status)
    assert (output_dir / "1.md").read_text(encoding = "utf-8") == expected


class FakeResponse:
    """
    A minimal stand-in for a `requests.Response`.
    """

    def __init__(self, statuses, links = None, error = None):
        """
        Create a fake response.

        ## Parameters

        - `statuses`: List of status dicts returned by `json()`
        - `links`: Dict of parsed Link headers, e.g. `{"next": {"url": "..."}}`
        - `error`: Optional exception raised by `raise_for_status()`

        ## Returns

        None
        """
        self.statuses = statuses
        self.links    = links if links is not None else {}
        self.error    = error


    def json(self):
        """
        Return the statuses.

        ## Returns

        The list of status dicts
        """
        return self.statuses


    def raise_for_status(self):
        """
        Raise the given error, if there is one.

        ## Returns

        None
        """
        if self.error:
            raise self.error


def _install_fake_get(monkeypatch, responses):
    """
    Replace `bookmarks.requests.get` with a fake that serves queued responses.

    ## Parameters

    - `monkeypatch`: pytest monkeypatch fixture
    - `responses`: List of `FakeResponse` objects, returned in order

    ## Returns

    List that will be filled with a `(url, headers)` tuple for each call
    """
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        return responses.pop(0)

    monkeypatch.setattr(bookmarks.requests, "get", fake_get)
    return calls


def test_fetch_bookmarks_sends_token_and_returns_statuses(monkeypatch):
    """
    Test that fetch_bookmarks sends the token and returns the statuses.

    ## Parameters

    - `monkeypatch`: pytest monkeypatch fixture

    ## Returns

    None
    """
    statuses = [{"id": "1"}, {"id": "2"}]
    calls    = _install_fake_get(monkeypatch, [FakeResponse(statuses)])

    result = bookmarks.fetch_bookmarks("https://example.social", "tok")

    assert result == statuses
    assert len(calls) == 1
    assert calls[0][0] == "https://example.social/api/v1/bookmarks"
    assert calls[0][1] == {"Authorization": "Bearer tok"}


def test_fetch_bookmarks_follows_next_link(monkeypatch):
    """
    Test that fetch_bookmarks follows the next link and combines the pages.

    ## Parameters

    - `monkeypatch`: pytest monkeypatch fixture

    ## Returns

    None
    """
    next_url = "https://example.social/api/v1/bookmarks?max_id=5"
    page1    = FakeResponse([{"id": "6"}, {"id": "5"}], links = {"next": {"url": next_url}})
    page2    = FakeResponse([{"id": "4"}])
    calls    = _install_fake_get(monkeypatch, [page1, page2])

    result = bookmarks.fetch_bookmarks("https://example.social", "tok")

    assert result == [{"id": "6"}, {"id": "5"}, {"id": "4"}]
    assert len(calls) == 2
    assert calls[1][0] == next_url
    assert calls[1][1] == {"Authorization": "Bearer tok"}


def test_fetch_bookmarks_raises_on_http_error(monkeypatch):
    """
    Test that fetch_bookmarks raises when the response is an HTTP error.

    ## Parameters

    - `monkeypatch`: pytest monkeypatch fixture

    ## Returns

    None
    """
    _install_fake_get(monkeypatch, [FakeResponse([], error = requests.HTTPError("401"))])

    with pytest.raises(requests.HTTPError):
        bookmarks.fetch_bookmarks("https://example.social", "tok")
