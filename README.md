# 微信公众号备份 wechat_official_backup

本仓库用于备份我本人公众号《文不加点的张衔瑜》的已发布/草稿/素材内容到 GitHub，便于归档与审阅。

### 命名规范
- 文章 Markdown 文件名：`YYYY-MM-DD 标题.md`
- 若同名冲突，将自动生成 `YYYY-MM-DD 标题 (2).md`、`(3).md` 等。

### 目录结构
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

### 凭据配置（本地）
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

### 本地运行
两种方式（二选一）：
- 使用命令行参数（优先级更高）
```bash
python scripts/backup_wechat.py --appid <你的APPID> --secret <你的APPSECRET> --account-name "文不加点的张衔瑜"
```
- 使用 `.env`（已配置时可直接）：
```bash
python scripts/backup_wechat.py
```

### CI 说明（已禁用）
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

### GitHub 仓库 Secrets（CI使用）
- `WECHAT_APPID`
- `WECHAT_APPSECRET`
（若仅在本地使用，可不在 Secrets 中配置）

### 本地备份分支策略（建议）
- 每次备份固定一个时间段（例如 2024-01 ~ 2024-06），从 `master` 新建特性分支，命名示例：
  - `backup/2024H1`
  - `backup/2024Q3`
  - `backup/2025-01-01_to_2025-03-31`
- 在该分支运行脚本、生成内容后：
  - 自查差异，提交并推送
  - 发起 PR 合并到 `master`，便于审阅

### Fork 使用建议（公开仓库）
- 仅代码（不含我的文章备份）：fork 后只保留 `master` 或仅保留 `scripts/`、`requirements.txt`，并清空 `content/`、`assets/`、`data/snapshots/`
- 仅备份内容（不含代码）：fork 后删除 `scripts/` 与 CI，仅同步 `content/`、`assets/`、`data/snapshots/`
- 全量：保留所有分支与目录结构

### 备注
- 该仓库仅备份我本人公众号内容；请确保你拥有备份目标账号的合法权限。
