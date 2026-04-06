[English](README_EN.md) | 简体中文

# BXI Robotics Wiki

BXI Robotics 开发者文档中心，基于 **MkDocs Material** 构建，支持中英双语，通过 GitHub Actions 自动部署到服务器。

- 在线文档：[wiki.bxirobotics.cn](https://wiki.bxirobotics.cn)

---

## 部署流程

本仓库已配置 GitHub Actions 自动化流水线，**无需在本地执行 `mkdocs build`**。

1. 在本地编辑或新增 Markdown 文件
2. `git push` 到 `master` 分支

推送后，GitHub Actions 会自动将 `docs/`、`mkdocs.yml`、`requirements.txt` 通过 SCP 同步到服务器，然后执行 `docker compose restart` 重启 MkDocs 容器。容器启动时依据 `requirements.txt` 安装依赖并实时渲染页面。

---

## 本地预览

```bash
# 创建并激活虚拟环境（仅首次）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（仅首次）
pip install -r requirements.txt

# 启动本地预览服务器
mkdocs serve
```

访问 `http://127.0.0.1:8000` 即可实时预览。

---

## 文档结构

本项目使用 **i18n suffix 模式**：中英文文件放在同一目录下，通过文件名后缀区分语言。

```
docs/
├── assets/                  # 全站共享静态资源（图片等）
│   ├── elf3/
│   ├── actuators/
│   └── ...
├── .nav.yml                 # 根级导航配置（含 use_index_title: true）
├── home.zh.md               # 中文首页
├── home.en.md               # 英文首页
│
├── elf3/
│   ├── .nav.yml             # 控制子项排序，不含 index.md
│   ├── index.zh.md          # 仅含 title frontmatter，提供 section 名称
│   ├── index.en.md          # 仅含 title frontmatter
│   ├── overview.zh.md       # 产品介绍内容
│   ├── overview.en.md
│   ├── quick_start.zh.md    # 操作指南内容
│   ├── quick_start.en.md
│   └── developer/
│       ├── .nav.yml
│       ├── index.zh.md      # 仅含 title frontmatter
│       ├── index.en.md
│       ├── navigation.zh.md
│       └── navigation.en.md
│
├── actuators/
│   ├── .nav.yml
│   ├── index.zh.md          # 仅含 title frontmatter
│   ├── index.en.md
│   ├── can_communication.zh.md
│   └── ...
└── ...
```

### index 文件的特殊规则

每个栏目目录下都有一对 `index.zh.md` / `index.en.md`，**只包含 frontmatter title，无正文内容**：

```markdown
---
title: 精灵3 人形机器人
---
```

这两个文件**不出现在导航菜单中**，仅用于提供该栏目在导航栏的中英文显示名称（由根 `.nav.yml` 的 `use_index_title: true` 读取）。

### 文件命名规范

| 规则 | 说明 |
|------|------|
| 文件夹名 / 文件名 | 只允许小写字母、数字、`_`、`-`，**禁止使用中文或空格** |
| 中文文档 | `文件名.zh.md` |
| 英文文档 | `文件名.en.md` |
| 共享资源 | 统一放在 `docs/assets/对应产品/` 下，不重复存放 |

---

## 新增内容

### 新增一篇文章

在对应目录下同时创建中英文文件即可，无需修改任何配置：

```
docs/elf3/new_page.zh.md
docs/elf3/new_page.en.md
```

### 新增一个栏目

1. 创建目录结构：

```
docs/half_robot/
├── .nav.yml             # 控制子项排序，不含 index.md
├── index.zh.md          # 仅 title: 半人形机器人
├── index.en.md          # 仅 title: Half Robot
├── overview.zh.md       # 栏目第一篇文章（内容）
├── overview.en.md
└── pnd_adam_u_sdk/
    ├── .nav.yml
    ├── index.zh.md      # 仅 title: PND Adam U SDK
    ├── index.en.md
    └── ...
```

2. 在上级 `.nav.yml` 加入目录名：

```yaml
# docs/.nav.yml
use_index_title: true

nav:
  - index.md
  - elf3
  - half_robot    # 新加这一行
  - actuators
  - ...
```

---

## 导航配置（`.nav.yml`）

每个目录有一个 `.nav.yml`，控制该目录下的导航顺序。**不要在 `nav:` 中列出 `index.md`**（index 不在菜单中显示）。

```yaml
# docs/elf3/.nav.yml
nav:
  - overview.md       # 写不带语言后缀的逻辑名，插件自动匹配当前语言
  - quick_start.md
  - developer
```

---

## 插图引用

所有图片统一存放在 `docs/assets/` 下，使用相对路径引用：

```markdown
![说明文字](../assets/elf3/demo.png)
```

**禁止**在中英文目录下各存一份相同图片。
