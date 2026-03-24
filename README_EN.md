[简体中文](README.md) | English

# BXI Robotics Wiki (Developer Documentation Repository)

Welcome to the central BXI Robotics Wiki code repository. This documentation architecture is powered by the **MkDocs Material** theme supplemented by advanced extensions, seamlessly driving multi-language environments (Chinese and English) and deployed entirely autonomously to 1Panel containers via GitHub Actions.

---

## 🛠️ Documentation Workflow: How Is Code Brought to Live Stages?

Thanks to the automated GitHub CI pipelines pre-configured under `.github/workflows/deploy.yml`, authors will **never** need to execute complex `mkdocs build` protocols explicitly on local rigs. Editing proceeds painlessly through two main steps:

1. Maintain or draft your new Markdown files.
2. Form a commit and enact `git push` directly onto `master` or `main`.

**Automated Deep Mechanics**: As a push is intercepted, GitHub synchronizes non-compiled, bare-bone references (`docs/`, `mkdocs.yml`, `requirements.txt`) directly via SCP onto the 1Panel volume mount paths. Post synchronization, an overarching SSH command triggers a restart logic for the active MkDocs docker suite running live in the data-center nodes. Upon spin-up, the container recursively checks into our `requirements` map dynamically and caches extensions securely before mounting an agile layout in memory.

---

## 📂 Page Routing & Bilingual File Tree Structure

As our engine governs translated sites context, documents are strictly silo-ed beneath the respective language root node folders preventing indexing cross-contamination. Meanwhile, binary/media items leverage a shared overarching parent vault for re-usability.

```text
docs/
├── assets/          <-- ★ Global Shared Content (Images, Videos, CADs)
│   ├── elf3/
│   └── ...
├── zh/              <-- 🇨🇳 Main Chinese Translation Source
│   ├── elf3/
│   │   ├── index.md         <-- Fallback root gateway
│   │   └── quick_start.md   <-- Supplemental sub-sheet
│   └── index.md
└── en/              <-- 🇬🇧 Main English Translation Source
    ├── elf3/
    └── index.md
```

### 1. Markdown Core Standards
Contributions must follow the fundamental Markdown guidelines.
- **Global Image Referencing**: **Never duplicate matching media blobs twice into separated directories**. Route the source file into the unifying `docs/assets/[Sub-Series_Name]/` library and invoke the relative exit path to pull the asset onto current domains reliably:
  `![Descriptive Tagging](../../assets/elf3/demo.jpg)`

### 2. Spawning New Index Categories & Custom Filtering
The repository does **not** rely on authors performing manual updates towards maintaining the nested YAML `nav:` branch maps inside the settings configuration. Through utilizing the `awesome-nav` framework mechanism, MkDocs detects your branch layout context inherently!
- **Setting Up New Directory Routes**: Deploying a completely separate structural layer means just appending a folder matching the new product unit names, under `docs/zh` and inversely mapped inside `docs/en`, such as `dog1`.
- **Primary Sub-Link Requirement**: Keep in mind that inside any initialized content layer branch, an index root must be defined (thus ensuring you drop an `index.md` acting as the welcoming entry module).
- **Overriding Alphabetic Sort Constraints**: The automated crawler processes contents and organizes trees following strict alphabetic indexing rules. For circumstances requiring custom sorting (Ex: Pushing the "Quick Guide" link above the "Advanced Breakdown"), initialize a file named `.nav.yml` strictly inside the acting problematic directory carrying sorting overrides syntax:
  ```yaml
  nav:
    - index.md
    - quick_start.md
    - '*'
  ```
- **Customizing Top-Level Tab Names**: By default, the plugin extracts raw physical folder strings (e.g., `joint_module`) to render the top root tabs. To forcefully map proper capitalized names or localized translations, initialize a `.nav.yml` file within that specific subfolder defining solely the title metadata:
  ```yaml
  title: Joint Module
  ```
- **File-Level Title Overrides (Homepage Injection)**: To overwrite the display name of raw Markdown page entities (like swapping "index" text in the menu to read "Home"), seamlessly inject explicit YAML Frontmatter atop the exact file itself `index.md`:
  ```yaml
  ---
  title: Home
  ---
  ```

### 3. Naming Convention Formalities & URL Generations
1. **File / Folder Entities**: Restrict standard file naming mechanisms uniquely to lowercase alphabet digits merged consistently by an underscore `_` or dash `-` (`joint_module`, `quick_start.md`). Deployments integrating UTF8-encoded Chinese script variants natively inside raw filesystem entities generate unreadable URL parameters breaking active site structures inevitably!
2. **Dynamic Sidebar Headers Lookup Parsing**: Although the base filename inherits English characters dynamically, the interface abstracts these paths smartly. The sidebar menu actively pulls the first `# H1 Heading` literal mapping from internal markup document syntax. Should it be required to override external menu aliases distinctly from heading representations, utilize the top-line YAML block parameter insertion procedure (`frontmatter`):
   ```yaml
   ---
   title: Overridden Short Name For Explicit Sidebar Rendering
   ---
   ```
