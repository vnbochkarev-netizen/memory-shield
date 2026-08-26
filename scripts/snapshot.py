#!/usr/bin/env python3
"""memory-shield: snapshot — collect memory state into a self-contained digest.

Usage:
  python3 snapshot.py --memory <file_or_dir> [--out <dir>] [--label <name>]

Reads the given memory sources, masks secrets, and writes one dated digest
file that survives compaction. Secrets are replaced with placeholders.
"""
import argparse, datetime, os, re, sys

SECRET_PATTERNS = [
    re.compile(r'(?i)\b(sk-[A-Za-z0-9]{10,})\b'),
    re.compile(r'(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[^\s"\']{8,}'),
    re.compile(r'(?i)\b(ghp_|github_pat_|clh_|xox[bap]?-)[A-Za-z0-9_]+'),
]

def mask(line: str) -> str:
    for pat in SECRET_PATTERNS:
        line = pat.sub(lambda m: '🔒 ' + m.group(0)[:8] + '…', line)
    return line

def collect(paths, root):
    lines = []
    for p in paths:
        ap = os.path.join(root, p) if root and not os.path.isabs(p) else p
        if os.path.isfile(ap):
            try:
                with open(ap, 'r', encoding='utf-8', errors='ignore') as f:
                    lines.append(f"\n## {p}\n")
                    lines.extend(mask(l.rstrip()) for l in f)
            except OSError as e:
                lines.append(f"\n## {p}\n(unreadable: {e})\n")
        elif os.path.isdir(ap):
            for dp, _, fs in os.walk(ap):
                for fn in sorted(fs):
                    fp = os.path.join(dp, fn)
                    rel = os.path.relpath(fp, root or '.')
                    lines.append(f"\n## {rel}\n")
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            lines.extend(mask(l.rstrip()) for l in f)
                    except OSError as e:
                        lines.append(f"(unreadable: {e})\n")
        else:
            lines.append(f"\n## {p}\n(missing)\n")
    return lines

def main():
    ap = argparse.ArgumentParser(description="Memory snapshot (memory-shield)")
    ap.add_argument("--memory", nargs="+", required=True, help="file(s) or dir(s) to snapshot")
    ap.add_argument("--out", default="./memory_snapshots", help="output dir")
    ap.add_argument("--label", default="snapshot", help="snapshot label")
    args = ap.parse_args()

    root = os.path.commonpath([os.path.abspath(m) for m in args.memory]) \
        if len(args.memory) > 1 else os.path.dirname(os.path.abspath(args.memory[0]))
    os.makedirs(args.out, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = os.path.join(args.out, f"{args.label}-{ts}.md")

    body = collect(args.memory, root)
    header = [
        f"# Memory snapshot — {args.label}",
        f"taken: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"sources: {', '.join(args.memory)}",
        "secrets: masked (🔒 placeholder)\n",
    ]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        f.write("\n".join(body) + "\n")
    print(f"✅ snapshot: {out} ({len(body)} lines)")

if __name__ == "__main__":
    main()
