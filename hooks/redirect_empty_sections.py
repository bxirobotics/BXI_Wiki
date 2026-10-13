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
from html import escape
import json

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
    page.meta["robots"] = "noindex, follow"

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
        is_en = alternate["lang"] == "en"
        title = "ELF3 Humanoid Robot Documentation and Developer Guides" if is_en else "ELF3 人形机器人使用文档与开发指南入口"
        description = (
            "Open the BXI ELF3 documentation for robot specifications, safe operation, ROS2 development, joint actuator interfaces and control software integration guides."
            if is_en else
            "进入半醒科技 ELF3 人形机器人文档，查阅整机规格、开箱操作、安全须知、ROS2 开发、关节电机通信与控制软件指南。本页将自动跳转到产品介绍，也可通过正文链接继续访问。"
        )
        canonical = config.site_url.rstrip("/") + alternate["link"] + "elf3/overview/"
        target.write_text(
            f'<!doctype html><html lang="{escape(alternate["lang"])}"><head>'
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)} - BXI Robotics</title>'
            f'<meta name="description" content="{escape(description)}">'
            f'<link rel="canonical" href="{escape(canonical)}">'
            '<script>location.replace("elf3/overview/"+location.search+location.hash);</script>'
            '<meta http-equiv="refresh" content="0; url=elf3/overview/">'
            f'</head><body><h1>{escape(title)}</h1>'
            f'<p>{escape(description)}</p><a href="elf3/overview/">'
            f'{"Continue to ELF3 documentation" if is_en else "查看 ELF3 产品介绍"}</a></body></html>\n',
            encoding="utf-8",
        )

    # Keep old /en/ bookmarks after English becomes the unprefixed default.
    site_dir = Path(config.site_dir)
    for source in list(site_dir.rglob("index.html")):
        relative = source.relative_to(site_dir)
        if relative.parts[0] in {"en", "zh"}:
            continue
        path = "/" + relative.as_posix().removesuffix("index.html")
        canonical = config.site_url.rstrip("/") + path
        alias = site_dir / "en" / relative
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<title>Moved - BXI Robotics documentation</title>'
            '<meta name="robots" content="noindex, follow">'
            f'<link rel="canonical" href="{escape(canonical)}">'
            '<script>document.cookie="bxi_locale=en; Path=/; Max-Age=31536000; SameSite=Lax";'
            f'location.replace({json.dumps(path)}+location.search+location.hash);</script>'
            f'<meta http-equiv="refresh" content="0; url={escape(path)}">'
            '</head><body><h1>Documentation has moved</h1>'
            f'<a href="{escape(path)}">Continue to the English documentation</a></body></html>\n',
            encoding="utf-8",
        )
