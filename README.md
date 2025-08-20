# WeChat OA Backup to GitHub · 文不加点的张衔瑜

> 张衔瑜：
> 把公众号散落的，都收集。

将我自己的微信公众号文章（已发布/草稿/永久图文素材）通过 **官方接口** 定时拉取，转为 Markdown，并将图片本地化存到同一仓库；同时提供一键自动化工作流，便于长期归档与公开展示。

This repository backs up my own WeChat Official Account “文不加点的张衔瑜” to GitHub.
It aims to preserve published words with care and clarity, and to make change history reviewable.

## 功能
- ✅ 官方接口拉取：发布列表（freepublish）、草稿箱（draft）、永久图文素材（material/news）  
- ✅ HTML→Markdown 转换，图片**本地化**，避免外链失效  
- ✅ GitHub Actions **定时备份**与**增量提交**  
- ✅（可选）GitHub Pages 发布文章目录，供在线阅读  
- ✅ 代码与内容可分支获取，满足不同使用者

## 目录结构（主分支 `master`）/ Structure
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

### 命名规范
- 文章 Markdown 文件名：`YYYY-MM-DD 标题.md`
- 若同名冲突，将自动生成 `YYYY-MM-DD 标题 (2).md`、`(3).md` 等。

### 快速开始 · 凭据配置（本地）/ Credentials (Local)
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

### CI 说明（已禁用）/ CI (disabled by default)
- 仓库默认关闭 CI；若需要启用：
  1) 将 `.github/workflows.disabled/wechat-backup.yml` 移动到 `.github/workflows/`
  2) 在仓库 Secrets 配置 `WECHAT_APPID`、`WECHAT_APPSECRET`
  3) 如需定时运行，自行恢复 `on.schedule` 配置
  4) 默认会从 `master` 创建特性分支并自动创建 PR

  ### CI/PR 流程（已禁用，可自行配置）
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



### 分支说明

* **`master`**（默认）：仅代码与工作流（包含目录规范、最小示例）；适合开发者获取脚本与自动化。
* **`archive`**（内容分支）：只存文章 Markdown、图片与快照；适合读者直接浏览/检索文章；（可作为 GitHub Pages 源）。
* **`feature/backup_code_dev`**：开发分支，用于脚本更新与测试，通过 PR 合入 `master`。
* **`full`**（聚合分支，可选）：聚合 `master` + `archive` 的内容，方便“一键获取全部”。

> 只要代码：`git clone -b master --single-branch ...`
> 只要文章：`git clone -b archive --single-branch ...`
> 全部：`git clone ...` 或切到 `full` 分支。

### Fork 使用建议（公开仓库）/ Fork Recommendations
- 仅代码（不含我的文章备份）：fork 后只保留 `master` 或仅保留 `scripts/`、`requirements.txt`，并清空 `content/`、`assets/`、`data/snapshots/`
- 仅备份内容（不含代码）：fork 后删除 `scripts/` 与 CI，仅同步 `content/`、`assets/`、`data/snapshots/`
- 全量：保留所有分支与目录结构

## 许可
- 该仓库仅备份我本人公众号内容；请确保你拥有备份目标账号的合法权限。
* **代码**：MIT（或你指定的开源许可）。
* **内容（公众号文章及派生 Markdown/PDF/图片）**：默认保留所有权利，或选择 CC BY-NC-ND 4.0 等合适条款。
  在仓库根目录放置 `LICENSE`（代码）与 `CONTENT-LICENSE`（内容）分别声明。

## 致谢

* GitHub Actions 与 Pages
* 官方微信公众号接口