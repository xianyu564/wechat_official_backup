# WeChat OA Backup to GitHub · 文不加点的张衔瑜

> 张衔瑜：
> 把公众号散落的，都收集。

将我自己的微信公众号文章（已发布/草稿/永久图文素材）通过 **官方接口** 定时拉取，转为 Markdown，并将图片本地化存到同一仓库；同时提供一键自动化工作流，便于长期归档与公开展示。

This repository backs up my own WeChat Official Account “文不加点的张衔瑜” to GitHub.
It aims to preserve published words with care and clarity, and to make change history reviewable.

## 功能 / Features
- ✅ 官方接口拉取：发布列表（freepublish）、草稿箱（draft）、永久图文素材（material/news）  
- ✅ HTML→Markdown 转换，图片**本地化**，避免外链失效  
- ✅ GitHub Actions **定时备份**与**增量提交**  
- ✅（可选）GitHub Pages 发布文章目录，供在线阅读  
- ✅ 代码与内容可分支获取，满足不同使用者

## 目录结构（主分支 `master`）/ Structure (`master` branch)
```text
content/
  wechat/文不加点的张衔瑜/            # 文章 Markdown（按年份分目录生成）
assets/
  wechat/                             # 图片本地化（按年/文章ID）
data/
  snapshots/                          # 保留接口原始 JSON（审计/排错）
scripts/
  backup_wechat.py                    # 主脚本（发布/草稿/素材 → MD）
  utils_html.py                       # HTML → Markdown & 图片本地化
requirements.txt
.github/workflows.disabled/wechat-backup.yml   # CI 模板（已禁用）
```

### 命名规范 / Naming Convention
- 文章 Markdown 文件名：`YYYY-MM-DD 标题.md`
- 若同名冲突，将自动生成 `YYYY-MM-DD 标题 (2).md`、`(3).md` 等。

### 快速开始 · 凭据配置（本地）/ Quick Start · Credentials (Local)
1) 在仓库根目录新建 `.env`（已被 `.gitignore` 忽略，不会入库）：
```dotenv
WECHAT_APPID=YOUR_APPID_HERE
WECHAT_APPSECRET=YOUR_APPSECRET_HERE
WECHAT_ACCOUNT_NAME=文不加点的张衔瑜
```
可参照现有init.env执行

2) 安装依赖：
```bash
pip install -r requirements.txt
```

### 本地运行 / Local Usage
两种方式（二选一）：
- 使用命令行参数（优先级更高）
```bash
python scripts/backup_wechat.py --appid <你的APPID> --secret <你的APPSECRET> --account-name "文不加点的张衔瑜"
```
- 使用 `.env`（已配置时可直接）：
```bash
python scripts/backup_wechat.py
```
- **时间范围备份：** 支持 `--from-date YYYY[-MM[-DD]]` 和 `--to-date YYYY[-MM[-DD]]`。
  - 示例：`python scripts/backup_wechat.py --from-date 2024-03 --to-date 2024-06`

### CI 说明（已禁用）/ CI (disabled by default)
- 仓库默认关闭 CI；若需要启用：
  1) 将 `.github/workflows.disabled/wechat-backup.yml` 移动到 `.github/workflows/`
  2) 在仓库 Secrets 配置 `WECHAT_APPID`、`WECHAT_APPSECRET`
  3) 如需定时运行，自行恢复 `on.schedule` 配置
  4) 默认会从 `master` 创建特性分支并自动创建 PR

### CI/PR 流程（已禁用，可自行配置）/ CI/PR Flow (disabled, configurable)
- 触发方式：
  - 手动触发（Actions → Run workflow）
  - 每周二 15:00（北京时间，UTC 07:00）自动运行
- 运行步骤：
  1) 从 `master` 新建特性分支 `backup/run-YYYYMMDD-HHMMSS`
  2) 执行备份脚本，产生的 `content/`、`assets/`、`data/snapshots/` 变更会被提交并推送
  3) 自动向 `master` 发起 PR，便于人工审阅与合并

### GitHub 仓库 Secrets（CI使用）/ GitHub Secrets (for CI)
- `WECHAT_APPID`
- `WECHAT_APPSECRET`
（若仅在本地使用，可不在 Secrets 中配置）

### 分支策略 / Branch Strategy
本仓库采用多分支策略，以满足不同使用场景和内容管理需求：

1.  **`master`**（默认分支）：
    - **用途：** 存储**核心代码**（`scripts/`、`requirements.txt`、`.gitignore`、`LICENSE`）以及文档（`README.md`、`docs/`）。
    - **特点：** 保持精简、稳定，适合开发者快速获取工具代码，或作为 GitHub Pages 的源码分支（若仅发布代码相关内容）。
    - **获取：** `git clone -b master --single-branch <repo_url>`

2.  **`archive`**（内容归档分支）：
    - **用途：** 专门用于存储**公众号文章备份内容**（`content/`、`assets/`、`data/snapshots/`）。
    - **特点：** 随着备份的进行，此分支会持续增长，适合读者直接浏览文章内容，或作为 GitHub Pages 的内容源（若发布文章）。
    - **获取：** `git clone -b archive --single-branch <repo_url>`
    - **管理：** 备份脚本的产出应合并到此分支。

3.  **`feature/backup_code_dev`**（开发分支）：
    - **用途：** 用于脚本功能开发、重构、测试等**代码层面的迭代**。
    - **特点：** 临时性开发工作区，代码测试成熟后通过 PR 合并到 `master`。
    - **获取：** `git checkout -b feature/backup_code_dev master` （从 `master` 创建）

4.  **`backup/run-YYYYMMDD-HHMMSS`**（自动化备份 PR 分支，由 CI 自动创建）：
    - **用途：** CI 每次运行时自动创建，包含**当次备份的所有增量内容**，用于向 `archive` 分支发起 PR。
    - **特点：** 生命周期短暂，仅为 PR 审核而存在，合并后可删除。

### Fork 使用建议（公开仓库）/ Fork Recommendations
根据你的需求，选择不同的 Fork 策略：

- **仅获取代码（不含我的文章备份）**：
  - Fork 后，可直接使用 `master` 分支。若不需要文章内容，清空 `content/`、`assets/`、`data/snapshots/` 目录。
  - 你的 CI 可配置为只保留 `scripts/` 和 `requirements.txt` 相关路径。
  - `git clone -b master --single-branch <你的fork_url>`

- **仅获取文章内容（不含代码）**：
  - Fork 后，切换到 `archive` 分支（如果已创建），并清理 `scripts/` 和 CI 配置文件。
  - `git clone -b archive --single-branch <你的fork_url>`

- **获取所有内容（包括代码与所有文章备份）**：
  - 直接 Fork 仓库，然后 `git clone <你的fork_url>`。你将获得所有分支和全部历史。

### 许可 / License
本仓库的许可区分**代码**与**内容**：

- **代码**：采用 MIT 许可证。
- **内容（公众号文章及派生 Markdown/PDF/图片）**：
  - 采用 CC BY-NC-ND 4.0（署名-非商业-禁止演绎）。
  - **个人浏览或研究用途**：允许在**注明来源**（“《文不加点的张衔瑜》”与本仓库链接）的前提下使用。
  - **商业/出版使用**：包括企业主体公众号、盈利性刊物、付费平台等，一律**需事先取得书面授权**。
  - **禁止演绎**：未经书面许可，不得改编、再创作或制作衍生作品。
  - 第三方商标或材料可能受其各自许可约束，本文档不授予相应权利。
  - 代码许可证文件为 `LICENSE`（仅限代码，MIT），内容许可为 `CONTENT-LICENSE`（非代码内容，CC BY-NC-ND 4.0）。

### 致谢 / Acknowledgements
* GitHub Actions 与 Pages
* 官方微信公众号接口
* `BeautifulSoup` & `html2text` & `requests` & `python-dotenv`