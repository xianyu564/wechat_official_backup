# Architecture & Data Flow

## 1. Overview

This repository provides a Python-based solution for backing up WeChat Official Account (OA) articles. The process involves fetching article data from WeChat's Open Platform APIs, transforming HTML content to Markdown, localizing images, and structuring the output for easy archival on GitHub.

## 2. Data Sources

- **WeChat Official Account API:**
  - `freepublish/batchget`: Retrieves list of published articles.
  - `freepublish/getarticle`: Fetches full content for specific published articles.
  - `draft/batchget`: Retrieves articles from the draft box.
  - `material/batchget_material`: Retrieves permanent news material.
  - `token`: Obtains `access_token` for API authentication.

## 3. Data Flow

1.  **Authentication:**
    - The script first obtains an `access_token` using `APPID` and `APPSECRET` from WeChat's API. Credentials are provided via environment variables (for CI) or `.env` file (for local use).
    - The `access_token` has a limited validity period (approx. 7200 seconds) and is managed per script run.

2.  **Article Fetching:**
    - The script iteratively calls WeChat APIs (e.g., `freepublish/batchget`) to retrieve articles in batches (typically 20 per call).
    - A simple rate limiting (0.2-second sleep between requests) is implemented to avoid hitting API frequency limits.
    - For published articles, if `batchget` doesn't return full content, a separate `freepublish/getarticle` call is made.

3.  **Snapshot Archival:**
    - Raw JSON responses from WeChat APIs are saved as timestamped `.json` files in `data/snapshots/`. This provides an auditable trail and allows for debugging or reprocessing if needed.

4.  **Content Transformation & Localization:**
    - HTML content of articles is parsed using `BeautifulSoup`.
    - Images referenced in the HTML (`<img>` tags with `src` or `data-src`) are downloaded and stored locally in `assets/wechat/<year>/<article_id>/`.
    - Image `src` attributes in the HTML are rewritten to relative paths (e.g., `/assets/wechat/...`) suitable for rendering on GitHub Pages.
    - The modified HTML is then converted to Markdown using `html2text`, preserving links and images.

5.  **Markdown Generation:**
    - Each article's Markdown content is saved to `content/wechat/<account_name>/<year>/`.
    - Filenames follow the `YYYY-MM-DD Title.md` format. Conflict resolution is handled by appending `(2)`, `(3)`, etc.
    - A YAML Front Matter is added to each Markdown file, including `title`, `date`, `source URL`, `platform`, and `article_id`.

## 4. GitHub Integration (CI/CD)

*(Note: CI is disabled by default. Refer to `README.md` for enabling instructions.)*

When CI is enabled, the GitHub Actions workflow automates the backup:

1.  **Checkout:** Fetches the repository history (full depth for branch creation).
2.  **Python Setup:** Configures Python environment.
3.  **Install Dependencies:** Installs `requirements.txt` dependencies.
4.  **Feature Branch Creation:** Creates a new feature branch (e.g., `backup/run-YYYYMMDD-HHMMSS`) off `master` for each run.
5.  **Run Backup Script:** Executes `scripts/backup_wechat.py` with sensitive credentials passed via GitHub Secrets.
6.  **Commit & Push:** If changes are detected (`content/`, `assets/`, `data/snapshots/`), they are committed to the new feature branch and pushed to remote.
7.  **Open Pull Request:** Automatically creates a Pull Request from the new feature branch to `master` for review.

## 5. Branching Strategy (Recommended)

For ongoing backups, it is recommended to create a new feature branch for each backup interval (e.g., quarterly, semi-annually):

- `master`: The stable branch containing the latest reviewed and merged content.
- `feature/backup_<year><quarter>` (e.g., `backup/2025Q1`, `backup/2024H2`):
  - Created from `master`.
  - Articles within the specified time range are backed up here.
  - After review, this branch is merged back into `master`.

This approach ensures that changes are isolated, easily reviewable, and keeps the `master` branch clean and reliable.
