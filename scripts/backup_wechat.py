# -*- coding: utf-8 -*-
import os, re, json, time, pathlib, hashlib, requests
from datetime import datetime
from scripts.utils_html import html_to_markdown_with_local_images

# ===== 环境变量（GitHub Actions 中通过 Secrets 注入） =====
APPID  = os.environ["WECHAT_APPID"]
SECRET = os.environ["WECHAT_APPSECRET"]
ACCOUNT_NAME = os.getenv("WECHAT_ACCOUNT_NAME", "文不加点的张衔瑜")

# ===== 目录 =====
ROOT     = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR  = ROOT / "content" / "wechat" / ACCOUNT_NAME
IMG_ROOT = ROOT / "assets" / "wechat"
SNAP     = ROOT / "data" / "snapshots"
for p in (OUT_DIR, IMG_ROOT, SNAP): p.mkdir(parents=True, exist_ok=True)

# ===== 基础工具 =====
def slug(s: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fa5\- ]+", "", (s or "").strip()).replace(" ", "-")
    return re.sub(r"-{2,}", "-", s)[:80] or "untitled"

def http_get_json(url: str):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def http_post_json(url: str, payload: dict):
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def save_snapshot(prefix: str, obj: dict):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    (SNAP / f"{prefix}-{ts}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

def get_access_token() -> str:
    url = ("https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={APPID}&secret={SECRET}")
    js = http_get_json(url)
    if "access_token" not in js:
        raise RuntimeError(f"get token failed: {js}")
    return js["access_token"]

def write_markdown(dirpath: pathlib.Path, title: str, url: str, ts: int, article_id: str, idx: int, md: str):
    dirpath.mkdir(parents=True, exist_ok=True)
    dt = datetime.fromtimestamp(ts)
    name = f"{dt.strftime('%Y-%m-%d')}_{slug(title)}_{idx}_{article_id}.md"
    fm = [
        "---",
        f'title: "{(title or "无题").replace("\"", "\'")}"',
        f"date: {dt.isoformat()}",
        f"source: {url or ''}",
        "platform: wechat",
        f"article_id: {article_id}",
        "---",
        ""
    ]
    (dirpath / name).write_text("\n".join(fm) + (md or ""), encoding="utf-8")

# ===== 备份：已发布（freepublish） =====
def backup_published(token: str):
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

        for i, n in enumerate(news, start=1):
            title = n.get("title", "")
            url   = n.get("url", "")
            html  = n.get("content", "")
            md = html_to_markdown_with_local_images(html, ts, article_id, IMG_ROOT)
            year_dir = OUT_DIR / datetime.fromtimestamp(ts).strftime("%Y")
            write_markdown(year_dir, title, url, ts, article_id, i, md)

# ===== 备份：草稿箱（draft） =====
def backup_drafts(token: str):
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
                md = html_to_markdown_with_local_images(html, ts, media_id, IMG_ROOT)
                year_dir = OUT_DIR / "drafts" / datetime.fromtimestamp(ts).strftime("%Y")
                write_markdown(year_dir, title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20

# ===== 备份：永久图文素材（material/news） =====
def backup_material_news(token: str):
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
                md = html_to_markdown_with_local_images(html, ts, media_id, IMG_ROOT)
                write_markdown(OUT_DIR / "material", title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20

if __name__ == "__main__":
    token = get_access_token()  # 有效期约 7200 秒；每次运行获取一次足够。 :contentReference[oaicite:4]{index=4}
    backup_published(token)     # ✅ 已发布列表（推荐主路径） :contentReference[oaicite:5]{index=5}
    # 如需同步草稿/素材，取消下面两行注释：
    # backup_drafts(token)      # ✅ 草稿箱（no_content=0 带 HTML 正文） :contentReference[oaicite:6]{index=6}
    # backup_material_news(token)  # ✅ 永久图文素材（type=news） :contentReference[oaicite:7]{index=7}
