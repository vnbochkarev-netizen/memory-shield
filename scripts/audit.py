#!/usr/bin/env python3
"""memory-shield: audit — diff two snapshots and summarize memory changes.

Usage:
  python3 audit.py --before <snapshot.md> --after <snapshot.md>

Reports facts added / removed / modified, in plain language.
"""
import argparse, difflib, re, sys

def normalize(lines):
    """Strip headers, timestamps, and blank lines for stable comparison."""
    out = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith("## ") or s.startswith("# Memory snapshot"):
            continue
        if re.match(r'^(taken|sources|secrets):', s, re.I):
            continue
        out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser(description="Memory audit (memory-shield)")
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    args = ap.parse_args()

    with open(args.before, "r", encoding="utf-8", errors="ignore") as f:
        before = normalize(f.read().splitlines())
    with open(args.after, "r", encoding="utf-8", errors="ignore") as f:
        after = normalize(f.read().splitlines())

    sm = difflib.SequenceMatcher(None, before, after)
    added, removed, modified = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            added.extend(after[j1:j2])
        elif tag == "delete":
            removed.extend(before[i1:i2])
        elif tag == "replace":
            modified.extend(f"{before[i1]}  ->  {after[j1]}")

    print(f"AUDIT: {len(before)} lines -> {len(after)} lines")
    print(f"  ➕ added: {len(added)}")
    for x in added[:10]:
        print(f"     + {x[:120]}")
    print(f"  ➖ removed: {len(removed)}")
    for x in removed[:10]:
        print(f"     - {x[:120]}")
    print(f"  ✏️ modified: {len(modified)}")
    for x in modified[:10]:
        print(f"     ~ {x[:140]}")
    suspicious = [x for x in added if re.search(r'(?i)ignore (previous|prior|above)|override your|never mention', x)]
    if suspicious:
        print(f"  ⚠️ suspicious additions: {len(suspicious)} (run scan_poison)")
    print("SUMMARY:", f"{len(added)} added, {len(removed)} removed, {len(modified)} modified, "
          f"{len(suspicious)} suspicious" if suspicious else f"{len(added)} added, {len(removed)} removed, {len(modified)} modified, 0 suspicious")

if __name__ == "__main__":
    main()
