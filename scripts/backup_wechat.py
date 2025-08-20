# -*- coding: utf-8 -*-
import os, re, json, time, pathlib, hashlib, requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from scripts.utils_html import html_to_markdown_with_local_images
import argparse # 新增导入 argparse
from dotenv import load_dotenv
from typing import Optional # 修复：新增导入 Optional

# ===== 移除环境变量定义，改为通过参数传递 =====
# APPID  = os.environ["WECHAT_APPID"]
# SECRET = os.environ["WECHAT_APPSECRET"]
# ACCOUNT_NAME = os.getenv("WECHAT_ACCOUNT_NAME", "文不加点的张衔瑜")

# ===== 目录 =====
ROOT     = pathlib.Path(__file__).resolve().parents[1]
# OUT_DIR 和 IMG_ROOT 将在 main 函数中根据传入参数动态确定
# OUT_DIR  = ROOT / "content" / "wechat" / ACCOUNT_NAME
# IMG_ROOT = ROOT / "assets" / "wechat"
SNAP     = ROOT / "data" / "snapshots"
for p in (SNAP, ): p.mkdir(parents=True, exist_ok=True) # 仅 SNAP 目录需要预先创建

# ===== 基础工具 =====
SESSION = None  # 在 main 中初始化具备重试的会话
def slug(s: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fa5\- ]+", "", (s or "").strip()).replace(" ", "-")

def http_get_json(url: str):
    global SESSION
    client = SESSION or requests
    r = client.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def http_post_json(url: str, payload: dict):
    global SESSION
    client = SESSION or requests
    if SESSION is None:
        raise RuntimeError("SESSION is not initialized. Please initialize SESSION before making HTTP requests.")
    r = SESSION.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def http_post_json(url: str, payload: dict):
    global SESSION
    if SESSION is None:
    if SESSION is None:
        raise RuntimeError("SESSION is not initialized. Please initialize SESSION before making HTTP requests.")
    r = SESSION.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def save_snapshot(prefix: str, obj: dict):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    (SNAP / f"{prefix}-{ts}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

def get_access_token(appid: str, secret: str) -> str:
    url = ("https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={appid}&secret={secret}")
    js = http_get_json(url)
    if "access_token" not in js:
        raise RuntimeError(f"get token failed: {js}")
    return js["access_token"]

def create_retry_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def write_markdown(dirpath: pathlib.Path, title: str, url: str, ts: int, article_id: str, idx: int, md: str):
    dirpath.mkdir(parents=True, exist_ok=True)
    dt = datetime.fromtimestamp(ts)
    # 命名规则：YYYY-MM-DD + 文章标题（出现重名则追加 (2)、(3)...）
    def sanitize_filename(name: str) -> str:
        name = re.sub(r"[\\/:*?\"<>|]", "", name or "无题")
        name = re.sub(r"\s+", " ", name).strip()
        return name[:180]
    base = f"{dt.strftime('%Y-%m-%d')} {sanitize_filename(title)}"
    candidate = f"{base}.md"
    suffix = 2
    while (dirpath / candidate).exists():
        candidate = f"{base} ({suffix}).md"
        suffix += 1
    fm = [
        "---",
        f'title: "{(title or "无题").replace("\"", "\'")}"',
        f"date: {dt.isoformat()}",
        f"source: {url or ''}",
        f"platform: wechat",
        f"article_id: {article_id}",
        "---",
        ""
    ]
    (dirpath / candidate).write_text("\n".join(fm) + (md or ""), encoding="utf-8")

# ===== 备份：已发布（freepublish） =====
def backup_published(token: str, out_dir: pathlib.Path, img_root: pathlib.Path, start_ts: int | None = None, end_ts: int | None = None):
    all_items = []
    offset = 0
    while True:
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token={token}"
        js = http_post_json(url, {"offset": offset, "count": 20, "no_content": 0})
        save_snapshot(f"published-{offset}", js)
        items = js.get("item", [])
        all_items.extend(items)
        if len(items) < 20:
            break
        offset += 20
        time.sleep(0.2)  # 简单限速，避免触发频控

    # 遍历每条，写入 Markdown（必要时回退调用 getarticle 拿 content）
    for it in all_items:
        article_id = it.get("article_id") or hashlib.md5(json.dumps(it, ensure_ascii=False).encode()).hexdigest()[:10]
        content = it.get("content", {})
        ts = int(content.get("update_time") or content.get("create_time") or time.time())
        if start_ts is not None and ts < start_ts:
            continue
        if end_ts is not None and ts > end_ts:
            continue
        news = content.get("news_item", [])
        # 若 batchget 没带 content，可调用 getarticle 获取
        need_fetch = any(not n.get("content") for n in news)
        if need_fetch:
            url_ga = f"https://api.weixin.qq.com/cgi-bin/freepublish/getarticle?access_token={token}"
            ga = http_post_json(url_ga, {"article_id": article_id})
            save_snapshot(f"published-getarticle-{article_id}", ga)
            content = ga.get("content", content)
            news = content.get("news_item", news)
            time.sleep(0.2)

        for i, n in enumerate(news, start=1):
            title = n.get("title", "")
            url   = n.get("url", "")
            html  = n.get("content", "")
            md = html_to_markdown_with_local_images(html, ts, article_id, img_root)
            year_dir = out_dir / datetime.fromtimestamp(ts).strftime("%Y")
            write_markdown(year_dir, title, url, ts, article_id, i, md)

# ===== 备份：草稿箱（draft） =====
def backup_drafts(token: str, out_dir: pathlib.Path, img_root: pathlib.Path, start_ts: int | None = None, end_ts: int | None = None):
    offset = 0
    while True:
        url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
        js = http_post_json(url, {"offset": offset, "count": 20, "no_content": 0})
        save_snapshot(f"drafts-{offset}", js)
        items = js.get("item", [])
        for it in items:
            media_id = it.get("media_id", "draft")
            content = it.get("content", {})
            ts = int(content.get("update_time") or content.get("create_time") or time.time())
            if start_ts is not None and ts < start_ts:
                continue
            if end_ts is not None and ts > end_ts:
                continue
            for i, n in enumerate(content.get("news_item", []), start=1):
                title = n.get("title", "")
                url   = n.get("url", "")
                html  = n.get("content", "")
                md = html_to_markdown_with_local_images(html, ts, media_id, img_root)
                year_dir = out_dir / "drafts" / datetime.fromtimestamp(ts).strftime("%Y")
                write_markdown(year_dir, title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20
        time.sleep(0.2)

# ===== 备份：永久图文素材（material/news） =====
def backup_material_news(token: str, out_dir: pathlib.Path, img_root: pathlib.Path, start_ts: int | None = None, end_ts: int | None = None):
    offset = 0
    while True:
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={token}"
        js = http_post_json(url, {"type": "news", "offset": offset, "count": 20})
        save_snapshot(f"materials-{offset}", js)
        items = js.get("item", [])
        for it in items:
            media_id = it.get("media_id", "news")
            content = it.get("content", {})
            ts = int(content.get("update_time") or content.get("create_time") or time.time())
            if start_ts is not None and ts < start_ts:
                continue
            if end_ts is not None and ts > end_ts:
                continue
            for i, n in enumerate(content.get("news_item", []), start=1):
                title = n.get("title", "")
                url   = n.get("url", "")
                html  = n.get("content", "")
                md = html_to_markdown_with_local_images(html, ts, media_id, img_root)
                write_markdown(out_dir / "material", title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20
        time.sleep(0.2)

def main():
    parser = argparse.ArgumentParser(description="Backup WeChat Official Account articles")
    parser.add_argument("--appid", help="WeChat AppID")
    parser.add_argument("--secret", help="WeChat AppSecret")
    parser.add_argument("--account-name", default="文不加点的张衔瑜", help="WeChat Official Account name")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to backup (for content directory)")
    parser.add_argument("--from-date", dest="from_date", help="Filter start date (YYYY or YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--to-date", dest="to_date", help="Filter end date (YYYY or YYYY-MM or YYYY-MM-DD)")
    args = parser.parse_args()

    # 读取 .env（如存在）
    load_dotenv(override=False)
    appid = args.appid or os.getenv("WECHAT_APPID")
    secret = args.secret or os.getenv("WECHAT_APPSECRET")
    account_name = args.account_name or os.getenv("WECHAT_ACCOUNT_NAME", "文不加点的张衔瑜")
    if not appid or not secret:
        raise SystemExit("WECHAT_APPID/WECHAT_APPSECRET 未配置：请通过 --appid/--secret 或 .env 设置后重试\nWECHAT_APPID/WECHAT_APPSECRET not configured. Please set via --appid/--secret or .env file and try again.")

    # 根据命令行参数动态确定目录
    out_dir = ROOT / "content" / "wechat" / account_name
    img_root = ROOT / "assets" / "wechat"

    # 确保主目录存在
    out_dir.mkdir(parents=True, exist_ok=True)
    img_root.mkdir(parents=True, exist_ok=True)

    # 初始化具备重试能力的 Session
    global SESSION
    SESSION = create_retry_session()

    # 解析时间区间
    def parse_start(s: Optional[str]) -> Optional[int]:
        if not s:
            return None
        s = s.strip()
        try:
            if re.fullmatch(r"\d{4}", s):
                dt = datetime(int(s), 1, 1, 0, 0, 0)
            elif re.fullmatch(r"\d{4}-\d{2}", s):
                y, m = map(int, s.split("-"))
                dt = datetime(y, m, 1, 0, 0, 0)
            else:
                dt = datetime.fromisoformat(s)
            return int(dt.timestamp())
        except Exception:
            raise SystemExit(f"--from-date 无法解析: {s}")

    def parse_end(s: Optional[str]) -> Optional[int]:
        import calendar
        if not s:
            return None
        s = s.strip()
        try:
            if re.fullmatch(r"\d{4}", s):
                y = int(s)
                dt = datetime(y, 12, 31, 23, 59, 59)
            elif re.fullmatch(r"\d{4}-\d{2}", s):
                y, m = map(int, s.split("-"))
                last_day = calendar.monthrange(y, m)[1]
                dt = datetime(y, m, last_day, 23, 59, 59)
            else:
                # YYYY-MM-DD -> end of day
                base = datetime.fromisoformat(s)
                dt = datetime(base.year, base.month, base.day, 23, 59, 59)
            return int(dt.timestamp())
        except Exception:
            raise SystemExit(f"--to-date 无法解析: {s}")

    start_ts = parse_start(args.from_date)
    end_ts = parse_end(args.to_date)

    token = get_access_token(appid, secret)
    backup_published(token, out_dir, img_root, start_ts, end_ts)
    # backup_drafts(token, out_dir, img_root, start_ts, end_ts) # 如需同步草稿/素材，取消注释 # Uncomment to sync drafts/materials
    # backup_material_news(token, out_dir, img_root, start_ts, end_ts)

if __name__ == "__main__":
    main()
