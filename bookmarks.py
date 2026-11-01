import html
import pathlib
import re
import tomllib
import urllib.parse

import requests


def load_config(path) -> dict:
    """
    Load configuration from a TOML file.

    ## Parameters

    - `path`: Path to the TOML config file

    ## Returns

    Dictionary containing the parsed TOML configuration
    """
    with open(path, "rb") as f:
        return tomllib.load(f)


def html_to_text(content: str) -> str:
    """
    Convert HTML content to plain text.

    Uses only the standard library to strip HTML tags and unescape entities.

    ## Parameters

    - `content`: HTML content to convert

    ## Returns

    Plain text version of the HTML content
    """
    result = re.sub(r"<br\s*/?>", "\n", content)
    result = re.sub(r"</p>\s*<p>", "\n\n", result)
    result = re.sub(r"<[^>]+>", "", result)
    result = html.unescape(result)
    return result.strip()


def attachment_filename(status_id: str, attachment: dict) -> str:
    """
    Generate a filename for a media attachment.

    ## Parameters

    - `status_id`: The status ID
    - `attachment`: A Mastodon attachment dict with keys: id, url

    ## Returns

    Filename in the format `{status_id}-{attachment_id}{extension}`
    """
    url_path = urllib.parse.urlparse(attachment["url"]).path
    suffix   = pathlib.PurePosixPath(url_path).suffix
    return f"{status_id}-{attachment['id']}{suffix}"


def status_to_markdown(status: dict) -> str:
    """
    Convert a Mastodon status to markdown with YAML front matter.

    ## Parameters

    - `status`: A Mastodon status dict with keys: id, created_at, url, account,
      content, media_attachments

    ## Returns

    Markdown string with YAML front matter, content and an Obsidian embed for
    each attachment that has a url, ending with a single newline
    """
    author = f'"@{status["account"]["acct"]}"'
    date   = status["created_at"]
    url    = status["url"]
    blocks = [html_to_text(status["content"])]

    for attachment in status["media_attachments"]:
        if attachment.get("url"):
            filename = attachment_filename(status["id"], attachment)
            blocks.append(f"![[{filename}]]")

    body         = "\n\n".join(blocks)
    front_matter = f"---\nauthor: {author}\ndate: {date}\nurl: {url}\n---"
    return f"{front_matter}\n\n{body}\n"


def save_bookmarks(statuses: list[dict], output_dir) -> None:
    """
    Save Mastodon statuses as markdown files.

    Writes one markdown file per status to the specified directory. Creates the
    directory if it does not exist. Overwrites existing files.

    ## Parameters

    - `statuses`: List of Mastodon status dicts
    - `output_dir`: Directory to write markdown files to

    ## Returns

    None
    """
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents = True, exist_ok = True)

    for status in statuses:
        file_path = output_path / f"{status['id']}.md"
        file_path.write_text(status_to_markdown(status), encoding = "utf-8")


def save_attachments(statuses: list[dict], attachments_dir) -> None:
    """
    Download the media attachments of Mastodon statuses.

    Creates the directory if it does not exist. Skips attachments without a url
    and files that have already been downloaded. No headers are sent, so the
    access token is never exposed to media hosts.

    ## Parameters

    - `statuses`: List of Mastodon status dicts
    - `attachments_dir`: Directory to write attachment files to

    ## Returns

    None

    ## Raises

    - `requests.HTTPError`: If any download returns an HTTP error status
    """
    directory = pathlib.Path(attachments_dir)
    directory.mkdir(parents = True, exist_ok = True)

    for status in statuses:
        for attachment in status["media_attachments"]:
            if not attachment.get("url"):
                continue

            path = directory / attachment_filename(status["id"], attachment)
            if path.exists():
                continue

            response = requests.get(attachment["url"])
            response.raise_for_status()
            path.write_bytes(response.content)


def fetch_bookmarks(instance_url: str, token: str) -> list[dict]:
    """
    Fetch all bookmarked statuses from a Mastodon instance.

    Follows the `next` pagination links until there are no more pages.

    ## Parameters

    - `instance_url`: Base URL of the Mastodon instance
    - `token`: Access token for the Mastodon API

    ## Returns

    List of Mastodon status dicts

    ## Raises

    - `requests.HTTPError`: If any request returns an HTTP error status
    """
    headers = {"Authorization": f"Bearer {token}"}
    url     = instance_url.rstrip("/") + "/api/v1/bookmarks"
    results = []

    while url:
        response = requests.get(url, headers = headers)
        response.raise_for_status()
        results.extend(response.json())
        url = response.links.get("next", {}).get("url")

    return results


def main() -> None:
    """
    Load Mastodon bookmarks and save them to markdown files.

    Loads configuration from config.toml, fetches bookmarks from the instance,
    saves them to the output directory and downloads their attachments to the
    attachments directory, both as specified in the config.

    ## Returns

    None
    """
    config   = load_config("config.toml")
    statuses = fetch_bookmarks(config["instance_url"], config["access_token"])
    save_bookmarks(statuses, config["output_dir"])
    save_attachments(statuses, config["attachments_dir"])

    print(f"Saved {len(statuses)} bookmarks to {config['output_dir']}")


if __name__ == "__main__":
    main()
