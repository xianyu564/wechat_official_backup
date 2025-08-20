# Architecture & Data Flow

## 1. Overview

This repository provides a Python-based solution for backing up WeChat Official Account (OA) articles. The process involves fetching article data from WeChat's Open Platform APIs, transforming HTML content to Markdown, localizing images, and structuring the output for easy archival on GitHub.

About the OA / 关于公众号
- The OA is non-profit and personal in nature. It collects essays, images/photography, and layout explorations across mixed topics: life logs, travel notes, creative sparks, and occasional social commentary.
- 该公众号**不以盈利为目的**，以个人随笔为主，内容涵盖文字、图像/摄影、版式尝试，题材多元：生活记录、旅行随笔、灵感与社会观察等。

## 2. Data Sources

- **WeChat Official Account API:**
  - `freepublish/batchget`: Retrieves list of published articles.
  - `freepublish/batchget`：获取已发布文章列表。
  - `freepublish/getarticle`: Fetches full content for specific published articles.
  - `freepublish/getarticle`：获取指定已发布文章的完整内容。
  - `draft/batchget`: Retrieves articles from the draft box.
  - `draft/batchget`：获取草稿箱中的文章。
  - `material/batchget_material`: Retrieves permanent news material.
  - `material/batchget_material`：获取永久图文素材。
  - `token`: Obtains `access_token` for API authentication.
  - `token`：获取用于 API 认证的 `access_token`。

## 3. Data Flow

1.  **Authentication:**
    - The script first obtains an `access_token` using `APPID` and `APPSECRET` from WeChat's API. Credentials are provided via command-line arguments or `env.json` (local), and via environment variables/Secrets (for CI).
    - 脚本首先使用微信 API 中的 `APPID` 和 `APPSECRET` 获取 `access_token`。凭据通过命令行参数或根目录 `env.json`（本地），以及环境变量/Secrets（CI）提供。
    - The `access_token` has a limited validity period (approx. 7200 seconds) and is managed per script run.
    - `access_token` 有效期有限（约 7200 秒），在每次脚本运行时重新获取和管理。

2.  **Article Fetching:**
    - The script iteratively calls WeChat APIs (e.g., `freepublish/batchget`) to retrieve articles in batches (typically 20 per call).
    - 脚本迭代调用微信 API（例如 `freepublish/batchget`）分批次（通常每次 20 条）获取文章。
    - A simple rate limiting (0.2-second sleep between requests) is implemented to avoid hitting API frequency limits.
    - 实施了简单的速率限制（每次请求间隔 0.2 秒），以避免触发 API 频率限制。
    - For published articles, if `batchget` doesn't return full content, a separate `freepublish/getarticle` call is made.
    - 对于已发布的文章，如果 `batchget` 未返回完整内容，将单独调用 `freepublish/getarticle` 获取。

3.  **Snapshot Archival:**
    - Raw JSON responses from WeChat APIs are saved as timestamped `.json` files in `data/snapshots/`. This provides an auditable trail and allows for debugging or reprocessing if needed.
    - 微信 API 的原始 JSON 响应以带时间戳的 `.json` 文件形式保存在 `data/snapshots/` 目录中。这提供了可审计的记录，并便于调试或后续重新处理。

4.  **Content Transformation & Localization:**
    - HTML content of articles is parsed using `BeautifulSoup`.
    - 文章的 HTML 内容使用 `BeautifulSoup` 进行解析。
    - Images referenced in the HTML (`<img>` tags with `src` or `data-src`) are downloaded and stored locally in `assets/wechat/<year>/<article_id>/`.
    - HTML 中引用的图片（`<img>` 标签的 `src` 或 `data-src`）会被下载并本地存储在 `assets/wechat/<year>/<article_id>/` 目录下。
    - Image `src` attributes in the HTML are rewritten to relative paths (e.g., `/assets/wechat/...`) suitable for rendering on GitHub Pages.
    - HTML 中图片的 `src` 属性将被重写为适合在 GitHub Pages 上渲染的相对路径（例如，`/assets/wechat/...`）。
    - The modified HTML is then converted to Markdown using `html2text`, preserving links and images.
    - 修改后的 HTML 内容将使用 `html2text` 转换为 Markdown，同时保留链接和图片。

5.  **Markdown Generation:**
    - Each article's Markdown content is saved to `content/wechat/<account_name>/<year>/`.
    - 每篇文章的 Markdown 内容将保存到 `content/wechat/<account_name>/<year>/` 目录下。
    - Filenames follow the `YYYY-MM-DD Title.md` format. Conflict resolution is handled by appending `(2)`, `(3)`, etc.
    - 文件名遵循 `YYYY-MM-DD 标题.md` 格式。命名冲突通过附加 `(2)`、`(3)` 等后缀解决。
    - A YAML Front Matter is added to each Markdown file, including `title`, `date`, `source URL`, `platform`, and `article_id`.
    - 每个 Markdown 文件都会添加 YAML Front Matter，包括 `title`、`date`、`source URL`、`platform` 和 `article_id`。

## 4. GitHub Integration (CI/CD)

*(Note: CI is disabled by default. Refer to `README.md` for enabling instructions.)*
*(注：CI 默认禁用。请参阅 `README.md` 以获取启用说明。)*

When CI is enabled, the GitHub Actions workflow automates the backup:

1.  **Checkout:** Fetches the repository history (full depth for branch creation).
1.  **代码检出 (Checkout)：** 获取仓库历史记录（完整深度，以便创建分支）。
2.  **Python Setup:** Configures Python environment.
2.  **Python 环境设置 (Python Setup)：** 配置 Python 运行环境。
3.  **Install Dependencies:** Installs `requirements.txt` dependencies.
3.  **安装依赖 (Install Dependencies)：** 安装 `requirements.txt` 中定义的依赖。
4.  **Feature Branch Creation:** Creates a new feature branch (e.g., `backup/run-YYYYMMDD-HHMMSS`) off `master` for each run.
4.  **特性分支创建 (Feature Branch Creation)：** 每次运行都会从 `master` 分支创建一个新的特性分支（例如 `backup/run-YYYYMMDD-HHMMSS`）。
5.  **Run Backup Script:** Executes `scripts/backup_wechat.py` with sensitive credentials passed via GitHub Secrets.
5.  **运行备份脚本 (Run Backup Script)：** 执行 `scripts/backup_wechat.py`，敏感凭据通过 GitHub Secrets 传递。
6.  **Commit & Push:** If changes are detected (`content/`, `assets/`, `data/snapshots/`), they are committed to the new feature branch and pushed to remote.
6.  **提交与推送 (Commit & Push)：** 如果检测到更改（`content/`、`assets/`、`data/snapshots/`），这些更改将被提交到新的特性分支并推送到远程。
7.  **Open Pull Request:** Automatically creates a Pull Request from the new feature branch to `master` for review.
7.  **打开 Pull Request (Open Pull Request)：** 自动从新的特性分支向 `master` 分支发起 Pull Request 以供审查。

## 5. Branching Strategy (Recommended)

For ongoing backups, it is recommended to create a new feature branch for each backup interval (e.g., quarterly, semi-annually):

- `master`: The stable branch containing the latest reviewed and merged content.
- `master`：包含最新审查和合并内容的稳定分支。
- `feature/backup_<year><quarter>` (e.g., `backup/2025Q1`, `backup/2024H2`):
- `feature/backup_<年份><季度>`（例如，`backup/2025Q1`、`backup/2024H2`）：
  - Created from `master`.
  - 从 `master` 创建。
  - Articles within the specified time range are backed up here.
  - 指定时间范围内的文章将备份到此分支。
  - After review, this branch is merged back into `master`.
  - 审查后，此分支将合并回 `master`。

This approach ensures that changes are isolated, easily reviewable, and keeps the `master` branch clean and reliable.

## 6. Licensing / 许可

English
- Code: MIT (see `LICENSE`). Free to use, modify, and redistribute with notices preserved.
- Non-code content (WeChat articles, images/photography, derived Markdown/PDF, snapshots): CC BY-NC-ND 4.0 (see `CONTENT-LICENSE`). Personal viewing/research allowed with attribution; any commercial/publication use requires prior written authorization.

中文
- 代码：MIT（见 `LICENSE`）。可自由使用、修改与再发布，需保留版权与许可声明。
- 非代码内容（公众号文章、图片/摄影、派生 Markdown/PDF、快照）：CC BY-NC-ND 4.0（见 `CONTENT-LICENSE`）。个人浏览或研究用途在署名前提下允许；**任何商业或出版使用须事先书面授权**。
