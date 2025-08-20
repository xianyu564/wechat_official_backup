# wechat_official_backup

本仓库用于《文不加点的张衔瑜》公众号的迁移与备份。
This repository is meant for WeChat Official Account Backup.

目录结构建议（可调整）：
```text
wechat-backup/
 content/
   wechat/文不加点的张衔瑜/2025/  # 文章 Markdown
 assets/
   wechat/2025/                     # 本地化图片
 data/
   snapshots/                       # 原始 JSON 归档
 scripts/
   backup_wechat.py
 .github/workflows/wechat-backup.yml
```

使用说明（简要）：
- 本地运行：在仓库根目录执行 `python wechat-backup/scripts/backup_wechat.py --account "文不加点的张衔瑜" --year 2025`
- GitHub Actions：在仓库 Secrets 配置 `WECHAT_COOKIE`（如需登录态），工作流会定期拉取并提交变更。
