# Changelog

## 2025-XX-XX

- 初始化仓库，重命名主分支为 `master`。
- 设定 Git 忽略 `.env` 敏感文件。
- `scripts/backup_wechat.py` 重构，支持通过命令行参数传入 `APPID` 和 `AppSecret`。
- GitHub Actions 工作流调整为每周运行。

## 2025-07-01

- 文档新增“发布能力（freepublish）政策提示”：
  - 列出 `freepublish` 相关接口：`batchget`、`delete`、`get`、`getarticle`、`submit`。
  - 标注政策变化：自 2025-07 起，个人主体、企业主体未认证及不支持认证账号被回收该能力调用权限。
  - 影响说明：个人主体账号无法通过官方接口获取“已发布图文”，仓库起到合规与能力边界提示作用。

