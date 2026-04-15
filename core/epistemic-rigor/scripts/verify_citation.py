#!/usr/bin/env python3
"""Verify if a URL or arXiv ID exists."""

import argparse
import urllib.request
from urllib.error import URLError, HTTPError


def check_url(url: str) -> bool:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except (HTTPError, URLError) as e:
        print(f"Failed to access {url}: {e}")
        return False
    except Exception as e:
        print(f"Unknown error accessing {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Anti-hallucination checkpoint for citations.")
    parser.add_argument("--url", help="Direct URL to verify")
    parser.add_argument("--arxiv", help="arXiv ID to verify (e.g. 1706.03762)")
    args = parser.parse_args()

    if not args.url and not args.arxiv:
        print("Error: Must provide either --url or --arxiv")
        return 1

    urls_to_check = []
    if args.url:
        urls_to_check.append(args.url)
    if args.arxiv:
        urls_to_check.append(f"https://arxiv.org/abs/{args.arxiv}")

    all_valid = True
    for url in urls_to_check:
        print(f"Verifying {url} ...")
        if check_url(url):
            print("[OK] Source is reachable.")
        else:
            print("[HALLUCINATION WARNING] Source is unreachable. Do not assert this without further verification.")
            all_valid = False

    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
