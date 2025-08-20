#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(data: dict, file_path: Path) -> None:
    ensure_directory(file_path.parent)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_markdown(content: str, file_path: Path) -> None:
    ensure_directory(file_path.parent)
    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)


def simulate_fetch_articles(account: str, year: int) -> list[dict]:
    # 这里先放一个模拟数据结构，后续可接入真实抓取逻辑
    return [
        {
            "title": f"示例文章 - {account}",
            "date": f"{year}-01-01",
            "content": f"这是 {account} 在 {year} 年的示例文章内容。",
            "assets": [],
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup WeChat Official Account articles")
    parser.add_argument("--account", required=True, help="WeChat Official Account name")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to backup")
    args = parser.parse_args()

    repo_root = Path.cwd()
    project_root = repo_root / "wechat-backup"

    # 目录
    md_dir = project_root / "content" / "wechat" / args.account / str(args.year)
    assets_dir = project_root / "assets" / "wechat" / str(args.year)
    snapshots_dir = project_root / "data" / "snapshots"

    ensure_directory(md_dir)
    ensure_directory(assets_dir)
    ensure_directory(snapshots_dir)

    articles = simulate_fetch_articles(args.account, args.year)
    snapshot_file = snapshots_dir / f"{args.account}_{args.year}.json"
    save_json({"account": args.account, "year": args.year, "articles": articles}, snapshot_file)

    for idx, article in enumerate(articles, start=1):
        slug = f"{article['date'].replace('-', '')}-{idx:02d}"
        md_path = md_dir / f"{slug}.md"
        md = f"# {article['title']}\n\n{article['content']}\n"
        save_markdown(md, md_path)

    print(f"Saved {len(articles)} article(s) to {md_dir}")
    print(f"Snapshot saved to {snapshot_file}")


if __name__ == "__main__":
    main()


