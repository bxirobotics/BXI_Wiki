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
│   ├── joint_module/
│   └── ...
├── .nav.yml                 # 根级导航配置
├── index.zh.md              # 中文首页
├── index.en.md              # 英文首页
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

在对应目录下同时创建中英文文件：

```
docs/elf3/new_page.zh.md
docs/elf3/new_page.en.md
```

文件创建后 `awesome-nav` 自动扫描识别，**无需修改任何配置文件**。

### 新增一个栏目（二级分类）

1. 创建目录和必要文件：

```
docs/half_robot/
├── .nav.yml          # 可选，用于控制子项排序
├── index.zh.md       # 栏目首页（必须存在）
├── index.en.md
└── pnd_adam_u_sdk/
    ├── index.zh.md
    └── index.en.md
```

2. 在上级 `.nav.yml` 的 `nav:` 列表中加入该目录名：

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

每个目录可以有一个 `.nav.yml` 文件，控制该目录下的导航行为。

### 控制子项排序

```yaml
# docs/elf3/.nav.yml
nav:
  - index.md
  - quick_start.md
  - developer
```

`nav:` 中使用**不带语言后缀的逻辑名**（写 `index.md`，不写 `index.zh.md`），插件会自动解析为当前语言的对应文件。

### 控制导航栏显示名称

Section 的导航栏名称来自该目录 `index.md` 的 frontmatter `title:` 字段（需根目录 `.nav.yml` 中开启 `use_index_title: true`）。

在 `index.zh.md` 中：
```markdown
---
title: 精灵3 人形机器人
---
```

在 `index.en.md` 中：
```markdown
---
title: ELF3 Robot
---
```

### 单篇文章的显示名称

在文件顶部加 frontmatter：
```markdown
---
title: 操作指南
---
```

---

## 插图引用

所有图片统一存放在 `docs/assets/` 下，使用相对路径引用：

```markdown
![说明文字](../assets/elf3/demo.png)
```

**禁止**在中英文目录下各存一份相同图片。
