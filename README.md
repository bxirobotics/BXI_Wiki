[English](README_EN.md) | 简体中文

# BXI Robotics Wiki

BXI Robotics 开发者文档中心，基于 **MkDocs Material** 构建，支持中英双语，通过 GitHub Actions 自动部署到服务器。

- 在线文档：[wiki.bxirobotics.cn](https://wiki.bxirobotics.cn)

---

## 部署流程

本仓库已配置 GitHub Actions 自动化流水线，**无需在本地执行 `mkdocs build`**。

1. 在本地编辑或新增 Markdown 文件
2. `git push` 到 `master` 分支

推送后，GitHub Actions 会通过 SSH 使用 rsync，按内容校验和增量同步 `docs/`、`overrides/`、`hooks/`、`mkdocs.yml`、`requirements.txt` 和 `.git/`。未修改的图片、视频等文件不会重复上传；仓库中删除的文件会从对应目录清理，部署目标目录中的其他文件会保留。完整 Git 历史用于生成作者和更新时间信息。

同步成功后才执行 `docker compose restart`。同一时间只运行一个发布任务，日志中的 rsync 统计会显示实际传输的文件数和数据量。

服务器需要预先安装 `rsync`。流程沿用 `SERVER_HOST`、`SERVER_USER`、`SERVER_SSH_KEY` 和 `SERVER_PORT` 四个 GitHub Actions secrets；未设置端口时使用 `22`。连接或同步失败时，任务会停止，不执行容器重启。

---

## 本地预览

```bash
# 创建并激活虚拟环境（仅首次）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（仅首次）
pip install -r requirements.txt

# 启动本地预览服务器
mkdocs serve --livereload
```

访问 `http://127.0.0.1:8000` 即可实时预览。

请保留 `--livereload`，以启用自动刷新和本地视频分段读取支持，确保视频进度可以拖动。

---

## 文档结构

本项目使用 **i18n suffix 模式**：中英文文件放在同一目录下，通过文件名后缀区分语言。

```
docs/
├── assets/                        # 全站共享静态资源（图片等）
│   ├── elf3/
│   │   ├── quick_start/           # 图片按所属 md 文件名归类存放
│   │   ├── overview/
│   │   └── developer/
│   │       ├── motioncontrol/
│   │       └── overview/
│   ├── control/
│   │   ├── appguide/
│   │   └── toolguide/
│   ├── actuators/
│   │   └── Introduction/
│   │       ├── BXI5014-19/
│   │       ├── BXI5018-19/
│   │       ├── BXI7010-19/
│   │       └── BXI8515-19/
│   └── ...
├── .nav.yml                       # 根级导航配置（含 use_index_title: true）
├── index.zh.md                    # 中文首页
├── index.en.md                    # 英文首页
│
├── elf3/
│   ├── .nav.yml
│   ├── index.zh.md                # 仅含 title frontmatter，提供 section 名称
│   ├── index.en.md
│   ├── overview.zh.md
│   ├── overview.en.md
│   ├── quick_start.zh.md
│   ├── quick_start.en.md
│   └── developer/
│       ├── .nav.yml
│       ├── index.zh.md
│       ├── index.en.md
│       ├── overview.zh.md
│       ├── motioncontrol.zh.md
│       ├── navigation.zh.md
│       └── manipulation.zh.md     # （及各自对应的 .en.md）
│
├── control/
│   ├── .nav.yml
│   ├── index.zh.md
│   ├── index.en.md
│   ├── app_guide.zh.md            # BXI Control App 使用指南
│   ├── app_guide.en.md
│   ├── tool_guide.zh.md           # BXI Tool 电机上位机使用指南
│   └── tool_guide.en.md
│
├── actuators/
│   ├── .nav.yml
│   ├── index.zh.md
│   ├── index.en.md
│   ├── can_communication.zh.md
│   └── Introduction/
│       └── ...                    # 各电机型号介绍页
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
| 共享资源 | 放在 `docs/assets/<栏目>/<md文件名>/` 下，按文档归类，不重复存放 |

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
  - control
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

所有图片统一存放在 `docs/assets/` 下，**按所属 md 文件名创建子目录**，使用相对路径引用：

```markdown
![说明文字](../assets/elf3/quick_start/demo.png)
```

命名规则：`docs/assets/<栏目>/<md文件名>/图片文件`，例如 `docs/elf3/quick_start.zh.md` 的图片放在 `docs/assets/elf3/quick_start/` 下。

**禁止**在中英文目录下各存一份相同图片（中英文共用同一套图片）。
