# -*- coding: utf-8 -*-
import os, hashlib, pathlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import html2text
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

def html_to_markdown_with_local_images(html: str, ts: int, article_id: str, img_root: pathlib.Path):
    """
    1) 解析 <img>，把 data-src/src 的远程图片下载到本地
    2) 改写 <img src> 为仓库相对路径，保证 GitHub Pages 可展示
    3) 转 Markdown（保留链接/图片）
    """
    soup = BeautifulSoup(html or "", "html.parser")
    img_dir = img_root / datetime.fromtimestamp(ts).strftime("%Y") / article_id
    img_dir.mkdir(parents=True, exist_ok=True)

    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src:
            continue
        try:
            h = hashlib.md5(src.encode("utf-8")).hexdigest()[:12]
            ext = pathlib.Path(urlparse(src).path).suffix or ".jpg"
            local_path = img_dir / f"{h}{ext}"
            if not local_path.exists():
                r = requests.get(src, timeout=30)
                r.raise_for_status()
                local_path.write_bytes(r.content)
            rel = os.path.relpath(local_path, ROOT).replace("\\", "/")
            img["src"] = "/" + rel
            if img.has_attr("data-src"):
                img["data-src"] = img["src"]
        except Exception:
            # 忽略单张失败，继续
            continue

    # 转 Markdown
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = False
    md = h2t.handle(str(soup))
    return md
