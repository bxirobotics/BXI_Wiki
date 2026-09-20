"""
MkDocs hook: redirect empty section index pages to their first content page.

A section index is considered "empty" if its markdown body (after stripping
frontmatter) contains nothing but optional zero-width spaces.  This matches
the pattern used for index files that only exist to provide a section title
for the i18n plugin.

No configuration needed — adding a new section with the same empty-index
pattern will automatically be redirected.
"""

from pathlib import Path

_ZERO_WIDTH_SPACE = "\u200b"

# Maps section directory (e.g. "elf3") to the URL of the first nav page
# inside that directory. Populated by on_nav before any page is built.
_section_redirects: dict[str, str] = {}


def _is_empty_body(source: str) -> bool:
    """Return True if the markdown source has no real content after frontmatter."""
    body = source.strip()

    # Strip YAML frontmatter (--- ... ---)
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            body = body[end + 4:]

    return not body.replace(_ZERO_WIDTH_SPACE, "").strip()


def on_page_markdown(markdown, page, config, files, **kwargs):
    """Guarantee every page renders non-empty HTML.

    An empty body renders to an empty string, which crashes plugins that parse
    the rendered HTML (mkdocs-video does `lxml.html.fromstring(html)`).  This
    runs *before* `page.render` and before any `page_content` plugin, so the
    placeholder below is what those plugins see.

    Without this, every section index has to hand-carry an invisible
    zero-width space in its markdown — which is easy to forget when adding a
    new section (that is exactly what broke the grippers section).
    """
    if _is_empty_body(markdown):
        return f"{_ZERO_WIDTH_SPACE}\n"
    return markdown


def on_nav(nav, config, files, **kwargs):
    """Walk the nav tree and record the first page URL for each directory."""
    _section_redirects.clear()

    def walk(items):
        for item in items:
            if hasattr(item, "children") and item.children:
                walk(item.children)
            elif hasattr(item, "file") and item.file:
                src = item.file.src_path.replace("\\", "/").split("/")
                # Register the first page encountered under each ancestor directory
                for depth in range(1, len(src)):
                    dir_key = "/".join(src[:depth])
                    if dir_key not in _section_redirects:
                        _section_redirects[dir_key] = item.url

    walk(nav.items)


def on_page_content(html, page, config, files, **kwargs):
    src_path = page.file.src_path.replace("\\", "/")
    parts = src_path.split("/")

    # Skip the root index (e.g. index.zh.md at top level)
    if len(parts) < 2:
        return html

    filename = parts[-1]
    if not (filename.startswith("index.") and filename.endswith(".md")):
        return html

    # Read the source file to check whether it has real content
    try:
        with open(page.file.abs_src_path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError:
        return html

    if not _is_empty_body(source):
        return html

    # Look up the first content page for this directory
    dir_key = "/".join(parts[:-1])  # e.g. "elf3" or "actuators/Introduction"
    target_url = _section_redirects.get(dir_key)
    if not target_url:
        return html

    target = "/" + target_url.lstrip("/")

    # Return a lightweight redirect; the surrounding template still renders
    # so users with JS disabled also get the <meta> fallback.
    return (
        f'<script>window.location.replace("{target}");</script>\n'
        f'<noscript><meta http-equiv="refresh" content="0; url={target}"></noscript>\n'
    )


def on_post_build(config, **kwargs):
    """Make each locale root redirect to its ELF3 overview."""
    for alternate in config.extra["alternate"]:
        target = Path(config.site_dir, alternate["link"].strip("/"), "index.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            '<script>window.location.replace("elf3/overview/");</script>\n'
            '<noscript><meta http-equiv="refresh" content="0; url=elf3/overview/"></noscript>\n',
            encoding="utf-8",
        )
