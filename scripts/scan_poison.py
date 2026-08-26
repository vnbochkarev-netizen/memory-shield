#!/usr/bin/env python3
"""memory-shield: scan_poison — detect injected instructions and contradictions.

Usage:
  python3 scan_poison.py --memory <file_or_dir> [--report <file>]

Heuristic scanner: flags imperative instructions embedded in data,
contradictory facts, and import anomalies. Flags go to QUARANTINE —
nothing is deleted.
"""
import argparse, datetime, os, re, sys

INJECTION_PATTERNS = [
    (r'(?i)\bignore (all )?(previous|prior|above) (instructions|rules|system)\b', "looks injected"),
    (r'(?i)\byou (are|must|should|need to) (now |always )?(ignore|forget|override)\b', "override instruction"),
    (r'(?i)\b(disregard|forget) (your|all) (instructions|rules|training)\b', "disregard instruction"),
    (r'(?i)\b\[?system\]?[:：]\s*(you|ignore|now)\b', "system-role injection"),
    (r'(?i)\b(never|always) (mention|reveal|say|tell)\b', "hidden-behavior instruction"),
    (r'(?i)\brepeat (after me|the following)\b', "copy-paste injection"),
]
ANOMALY_RE = re.compile(r'(?i)(0x[0-9a-f]{8,}|%%|§{3,}|\x00)')

def scan_text(lines):
    flags = []
    for i, line in enumerate(lines, 1):
        for pat, why in INJECTION_PATTERNS:
            if re.search(pat, line):
                flags.append((i, "injected", why, line.strip()[:140]))
                break
        else:
            if ANOMALY_RE.search(line):
                flags.append((i, "anomaly", "suspicious marker", line.strip()[:140]))
    return flags

def scan_contradictions(lines):
    """key = value pairs: same key with clearly different values => contradiction."""
    kv = {}
    for i, line in enumerate(lines, 1):
        m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_ .\-]{2,40})\s*[:=]\s*(.+)$', line)
        if m:
            key, val = m.group(1).strip().lower(), m.group(2).strip().lower()
            if len(val) < 60:
                kv.setdefault(key, []).append((i, val))
    out = []
    for key, vals in kv.items():
        uniq = {v for _, v in vals}
        if len(uniq) > 1 and len(vals) > 1:
            out.append((vals[0][0], "contradiction",
                        f"same key '{key}' stored with different values", " | ".join(v for _, v in vals[:3])[:140]))
    return out

def main():
    ap = argparse.ArgumentParser(description="Poison scan (memory-shield)")
    ap.add_argument("--memory", nargs="+", required=True, help="file(s) or dir(s) to scan")
    ap.add_argument("--report", default="scan_report.md", help="output report")
    args = ap.parse_args()

    lines = []
    for p in args.memory:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    lines.extend(f.read().splitlines())
            except OSError as e:
                print(f"! {p}: {e}", file=sys.stderr)
        elif os.path.isdir(p):
            for dp, _, fs in os.walk(p):
                for fn in sorted(fs):
                    fp = os.path.join(dp, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            lines.extend(f.read().splitlines())
                    except OSError:
                        pass

    flags = scan_text(lines) + scan_contradictions(lines)
    total = len(lines)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(f"SCAN {now} — {total} lines checked\n")
        if flags:
            f.write(f"⚠️ QUARANTINE ({len(flags)}):\n")
            for i, kind, why, txt in flags:
                f.write(f"  #{i} [{kind}] {why}: {txt}\n")
        else:
            f.write("✅ CLEAN — no suspicious patterns detected\n")
    print(f"✅ scan done: {len(flags)} flags -> {args.report}")
    for i, kind, why, txt in flags[:10]:
        print(f"  #{i} [{kind}] {why}: {txt}")

if __name__ == "__main__":
    main()
