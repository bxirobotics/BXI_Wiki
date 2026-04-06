[简体中文](README.md) | English

# BXI Robotics Wiki

Developer documentation for BXI Robotics, built with **MkDocs Material**, supporting Chinese and English, and automatically deployed via GitHub Actions.

- Live site: [wiki.bxirobotics.cn](https://wiki.bxirobotics.cn)

---

## Deployment

This repository uses a GitHub Actions pipeline — **no local `mkdocs build` required**.

1. Edit or create Markdown files locally
2. `git push` to the `master` branch

After pushing, GitHub Actions syncs `docs/`, `mkdocs.yml`, and `requirements.txt` to the server via SCP, then runs `docker compose restart` to restart the MkDocs container. The container installs dependencies from `requirements.txt` and renders pages on startup.

---

## Local Preview

```bash
# Create and activate virtual environment (first time only)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start local preview server
mkdocs serve
```

Visit `http://127.0.0.1:8000` for a live preview.

---

## Project Structure

This project uses **i18n suffix mode**: Chinese and English files share the same directory, distinguished by filename suffix.

```
docs/
├── assets/                  # Shared static assets (images, etc.)
│   ├── elf3/
│   ├── joint_module/
│   └── ...
├── .nav.yml                 # Root navigation config
├── index.zh.md              # Chinese homepage
├── index.en.md              # English homepage
├── elf3/
│   ├── .nav.yml
│   ├── index.zh.md
│   ├── index.en.md
│   ├── quick_start.zh.md
│   ├── quick_start.en.md
│   └── developer/
│       ├── .nav.yml
│       ├── index.zh.md
│       └── index.en.md
├── actuators/
│   ├── .nav.yml
│   ├── index.zh.md
│   ├── index.en.md
│   └── ...
└── ...
```

### Naming Conventions

| Rule | Details |
|------|---------|
| Folder / file names | Lowercase letters, digits, `_`, `-` only — **no Chinese characters or spaces** |
| Chinese documents | `filename.zh.md` |
| English documents | `filename.en.md` |
| Shared assets | Place under `docs/assets/<product>/` — never duplicate |

---

## Adding Content

### Adding a new page

Create both language files in the target directory:

```
docs/elf3/new_page.zh.md
docs/elf3/new_page.en.md
```

`awesome-nav` auto-discovers new files — **no config changes needed**.

### Adding a new section (nested category)

1. Create the directory and required files:

```
docs/half_robot/
├── .nav.yml          # Optional — controls child item order
├── index.zh.md       # Section index page (required)
├── index.en.md
└── pnd_adam_u_sdk/
    ├── index.zh.md
    └── index.en.md
```

2. Add the directory name to the parent `.nav.yml`:

```yaml
# docs/.nav.yml
use_index_title: true

nav:
  - index.md
  - elf3
  - half_robot    # add this line
  - actuators
  - ...
```

---

## Navigation Config (`.nav.yml`)

Each directory can have a `.nav.yml` file to control its navigation behavior.

### Controlling item order

```yaml
# docs/elf3/.nav.yml
nav:
  - index.md
  - quick_start.md
  - developer
```

Use **locale-stripped logical names** in `nav:` (write `index.md`, not `index.zh.md`) — the plugin resolves them to the correct language file automatically.

### Setting section display names

Section names in the navigation come from the `title:` frontmatter field of that directory's `index.md` (requires `use_index_title: true` in the root `.nav.yml`).

In `index.zh.md`:
```markdown
---
title: 精灵3 人形机器人
---
```

In `index.en.md`:
```markdown
---
title: ELF3 Robot
---
```

### Setting individual page display names

Add frontmatter at the top of the file:
```markdown
---
title: Quick Start Guide
---
```

---

## Image References

All images go under `docs/assets/`. Reference them with relative paths:

```markdown
![Description](../assets/elf3/demo.png)
```

**Never** store duplicate copies of the same image under separate language directories.
