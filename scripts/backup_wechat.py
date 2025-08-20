# -*- coding: utf-8 -*-
import os, re, json, time, pathlib, hashlib, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from scripts.utils_html import html_to_markdown_with_local_images
import argparse # 新增导入 argparse

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
    return re.sub(r"-{2,}", "-", s)[:80] or "untitled"

def http_get_json(url: str):
    global SESSION
    client = SESSION or requests
    r = client.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def http_post_json(url: str, payload: dict):
    global SESSION
    client = SESSION or requests
    r = client.post(url, json=payload, timeout=30)
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
    name = f"{dt.strftime('%Y-%m-%d')}_{slug(title)}_{idx}_{article_id}.md"
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
    (dirpath / name).write_text("\n".join(fm) + (md or ""), encoding="utf-8")

# ===== 备份：已发布（freepublish） =====
def backup_published(token: str, out_dir: pathlib.Path, img_root: pathlib.Path):
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
def backup_drafts(token: str, out_dir: pathlib.Path, img_root: pathlib.Path):
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
def backup_material_news(token: str, out_dir: pathlib.Path, img_root: pathlib.Path):
    offset = 0
    while True:
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={token}"
        js = http_post_json(url, {"type": "news", "offset": offset, "count": 20})
        save_snapshot(f"materials-{offset}", js)
        items = js.get("item", [])
        for it in items:
            media_id = it.get("media_id", "news")
            content = it.get("content", {})
            ts = int(time.time())
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
    parser.add_argument("--appid", required=True, help="WeChat AppID")
    parser.add_argument("--secret", required=True, help="WeChat AppSecret")
    parser.add_argument("--account-name", default="文不加点的张衔瑜", help="WeChat Official Account name")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to backup (for content directory)")
    args = parser.parse_args()

    # 根据命令行参数动态确定目录
    out_dir = ROOT / "content" / "wechat" / args.account_name
    img_root = ROOT / "assets" / "wechat"

    # 确保主目录存在
    out_dir.mkdir(parents=True, exist_ok=True)
    img_root.mkdir(parents=True, exist_ok=True)

    # 初始化具备重试能力的 Session
    global SESSION
    SESSION = create_retry_session()

    token = get_access_token(args.appid, args.secret)
    backup_published(token, out_dir, img_root)
    # backup_drafts(token, out_dir, img_root) # 如需同步草稿/素材，取消注释
    # backup_material_news(token, out_dir, img_root)

if __name__ == "__main__":
    main()
