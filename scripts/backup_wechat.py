# scripts/backup_wechat.py
import os, re, json, time, pathlib, hashlib, requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup           # pip install beautifulsoup4
import html2text                        # pip install html2text

APPID  = os.environ["WECHAT_APPID"]
SECRET = os.environ["WECHAT_APPSECRET"]
ACCOUNT_NAME = os.getenv("WECHAT_ACCOUNT_NAME", "文不加点的张衔瑜")

ROOT    = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "content" / "wechat" / ACCOUNT_NAME
IMG_DIR = ROOT / "assets" / "wechat"
SNAP    = ROOT / "data" / "snapshots"
for p in (OUT_DIR, IMG_DIR, SNAP): p.mkdir(parents=True, exist_ok=True)

def get_access_token():
    url = ("https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={APPID}&secret={SECRET}")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    js = r.json()
    if "access_token" not in js:
        raise RuntimeError(f"get token failed: {js}")
    return js["access_token"], js["expires_in"]

def wechat_post(api, payload):
    token, _ = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/{api}?access_token={token}"
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    js = r.json()
    if js.get("errcode", 0) != 0 and "item" not in js:
        # 兼容 count 接口等无 errcode=0 也返回正常字段的情况
        raise RuntimeError(f"WX API error: {api} -> {js}")
    return js

def slug(s):
    s = re.sub(r"\s+", "-", re.sub(r"[^\w\u4e00-\u9fa5\- ]+", "", s.strip()))
    return re.sub(r"-{2,}", "-", s)[:80]

def html_to_md_and_save_images(article_id, html, ts):
    # 先把 <img> 本地化，再转 md，避免链接丢失
    soup = BeautifulSoup(html, "html.parser")
    img_dir = IMG_DIR / datetime.fromtimestamp(ts).strftime("%Y") / article_id
    img_dir.mkdir(parents=True, exist_ok=True)
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src: 
            continue
        try:
            fn = hashlib.md5(src.encode("utf-8")).hexdigest()[:12]
            ext = pathlib.Path(urlparse(src).path).suffix or ".jpg"
            local = img_dir / f"{fn}{ext}"
            if not local.exists():
                rr = requests.get(src, timeout=30)
                rr.raise_for_status()
                local.write_bytes(rr.content)
            # 改写为相对路径，便于 GitHub Pages
            rel = os.path.relpath(local, ROOT)
            img["src"] = "/" + rel.replace("\\", "/")
            # wechat 常见 data-src
            if img.has_attr("data-src"):
                img["data-src"] = img["src"]
        except Exception:
            continue
    html = str(soup)
    # 转 Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    md = h.handle(html)
    return md

def write_markdown(dirpath, title, url, ts, article_id, idx, md):
    dirpath.mkdir(parents=True, exist_ok=True)
    dt = datetime.fromtimestamp(ts)
    name = f"{dt.strftime('%Y-%m-%d')}_{slug(title)}_{idx}_{article_id}.md"
    fm = [
        "---",
        f'title: "{title.replace("\"", "\\\"")}"',
        f"date: {dt.isoformat()}",
        f"source: {url}",
        f"platform: wechat",
        f"article_id: {article_id}",
        "---",
        ""
    ]
    (dirpath / name).write_text("\n".join(fm) + md, encoding="utf-8")

def save_snapshot(prefix, obj):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    (SNAP / f"{prefix}-{ts}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

def backup_published():
    all_items = []
    offset = 0
    while True:
        js = wechat_post("freepublish/batchget", {"offset": offset, "count": 20})
        save_snapshot("published", js)
        items = js.get("item", [])
        all_items += items
        if len(items) < 20: break
        offset += 20

    for it in all_items:
        article_id = it.get("article_id") or hashlib.md5(json.dumps(it).encode()).hexdigest()[:10]
        content = it["content"]
        ts = int(content.get("update_time") or content.get("create_time") or time.time())
        news = content.get("news_item", [])
        for i, n in enumerate(news, start=1):
            title = n.get("title", "untitled")
            url   = n.get("url", "")
            html  = n.get("content", "")
            md = html_to_md_and_save_images(article_id, html, ts)
            write_markdown(OUT_DIR / datetime.fromtimestamp(ts).strftime("%Y"), title, url, ts, article_id, i, md)

def backup_drafts():
    # 可选：拉草稿箱全文（不需要的话可注释）
    offset = 0
    while True:
        js = wechat_post("draft/batchget", {"offset": offset, "count": 20, "no_content": 0})
        save_snapshot("drafts", js)
        items = js.get("item", [])
        for it in items:
            media_id = it.get("media_id", "draft")
            content = it.get("content", {})
            ts = int(content.get("update_time") or content.get("create_time") or time.time())
            for i, n in enumerate(content.get("news_item", []), start=1):
                title = n.get("title", "untitled")
                url   = n.get("url", "")
                html  = n.get("content", "")
                md = html_to_md_and_save_images(media_id, html, ts)
                write_markdown(OUT_DIR / "drafts" / datetime.fromtimestamp(ts).strftime("%Y"), title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20

def backup_material_news():
    # 可选：旧图文永久素材
    offset = 0
    while True:
        js = wechat_post("material/batchget_material", {"type": "news", "offset": offset, "count": 20})
        save_snapshot("materials", js)
        items = js.get("item", [])
        for it in items:
            media_id = it.get("media_id", "news")
            content = it.get("content", {})
            for i, n in enumerate(content.get("news_item", []), start=1):
                title = n.get("title", "untitled")
                url   = n.get("url", "")
                html  = n.get("content", "")
                ts = int(time.time())
                md = html_to_md_and_save_images(media_id, html, ts)
                write_markdown(OUT_DIR / "material", title, url, ts, media_id, i, md)
        if len(items) < 20: break
        offset += 20

if __name__ == "__main__":
    backup_published()       # 已发布（推荐）
    # backup_drafts()        # 可选
    # backup_material_news() # 可选
