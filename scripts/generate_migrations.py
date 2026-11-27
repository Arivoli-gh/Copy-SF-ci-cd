#!/usr/bin/env python3
"""
generate_migrations.py

Reads a list of Snowflake object names (one per line) and, for each line,
creates the next versioned schemachange file in the migrations folder, with the
database name replaced by {{ DATABASE }}. Lines that were processed are removed
from the list; lines that failed stay in the list with a "# FAILED:" comment.

File names follow the pattern  V<next version>__<prefix><YYYYMMDD>.sql
for example  V1.0.5__deployment20261124.sql
ALL objects of one run go into ONE file with ONE new version, in the order they
appear in the list (list tables before the views that depend on them). Objects
that fail stay in the list and are put into a later file when they succeed.

List file format (requests/objects.txt):
    # comment lines and blank lines are ignored
    DEMO_DEV.APP.CUSTOMERS
    DEMO_DEV.APP.CUSTOMER_ORDERS
    DEMO_DEV.APP.SALES_DT | DYNAMIC_TABLE          # optional "| TYPE"
    DEMO_DEV.APP.MY_PROC(VARCHAR, NUMBER)          # functions/procedures need arg types

Usage (run from the repository root):
    python scripts/generate_migrations.py --list-file requests/objects.txt \
        --migrations-dir migrations --connection snowflake
Optional: --prefix deployment   (text before the date, default "deployment")
          --date 20261124       (default: today's date, UTC)
Versions continue from the highest V<version>__ file found anywhere in the repo.
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from create_migration_file import build_content, fetch_ddl, next_version, split_name  # noqa: E402


def repo_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
        out += [os.path.join(d, f) for f in files]
    return out


def process(cur, lines, repo_root, migrations_dir, bump="patch", var="DATABASE", add_schema=True,
            prefix="deployment", date_tag=None):
    """Returns (created_files, failed [(name, reason)], lines_to_keep)."""
    date_tag = date_tag or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    known = repo_files(repo_root)
    created, failed, kept, seen = [], [], [], set()
    blocks = []                           # (name, type, original list line, generated SQL) for this run
    for raw in lines:
        s = raw.strip()
        if s.startswith("# FAILED:"):
            continue                      # old failure note; written again below if it fails again
        if not s or s.startswith("#"):
            kept.append(raw)
            continue
        name, _, typ = s.partition("|")
        name = name.split("#")[0].strip()
        typ = typ.split("#")[0].strip() or None
        key = (name.upper(), (typ or "").upper())
        if key in seen:
            print("Skipping duplicate line: " + name)
            continue
        seen.add(key)
        try:
            parts, _sig = split_name(name)
            obj_type, ddl = fetch_ddl(cur, name, typ)
            content, count, warns = build_content(name, obj_type, ddl, parts, var, add_schema)
            blocks.append((name, obj_type, raw, content))
            print("OK      %s (%s)  [%d database reference(s) parameterized]" % (name, obj_type, count))
            for w in warns:
                print("WARNING %s: %s" % (name, w))
        except Exception as exc:
            text = str(exc).strip()
            reason = (" ".join(text.split())[:240]) if text else exc.__class__.__name__
            failed.append((name, reason))
            kept += ["# FAILED: " + reason, raw]
            print("FAILED  %s: %s" % (name, reason), file=sys.stderr)
    if blocks:
        try:
            version = next_version(known, bump)
            fname = "V%s__%s%s.sql" % (version, prefix, date_tag)
            os.makedirs(migrations_dir, exist_ok=True)
            path = os.path.join(migrations_dir, fname)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(combine(blocks))
            created.append(path)
            print("Wrote %s with %d object(s)" % (fname, len(blocks)))
        except Exception as exc:          # nothing was written: keep every line for the next run
            reason = " ".join(str(exc).split())[:240] or exc.__class__.__name__
            for name, _t, raw, _c in blocks:
                failed.append((name, reason))
                kept += ["# FAILED: " + reason, raw]
                print("FAILED  %s: %s" % (name, reason), file=sys.stderr)
    return created, failed, kept


def combine(blocks):
    """One file for all objects, in list order (put tables before the views that use them).
    The CREATE SCHEMA line is written once per schema; each object keeps its own header comments."""
    out, seen_schema = [], set()
    for i, (name, _t, _raw, content) in enumerate(blocks, 1):
        kept_lines = []
        for line in content.split("\n"):
            if line.startswith("CREATE SCHEMA IF NOT EXISTS "):
                if line in seen_schema:
                    continue              # already created earlier in this file
                seen_schema.add(line)
            kept_lines.append(line)
        out.append("-- ===== %d/%d: %s =====\n" % (i, len(blocks), name) + "\n".join(kept_lines).rstrip("\n"))
    return "\n\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Create versioned migration files from a list of object names.")
    ap.add_argument("--list-file", default="requests/objects.txt")
    ap.add_argument("--migrations-dir", default="migrations")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--bump", choices=["patch", "minor", "major"], default="patch")
    ap.add_argument("--var-name", default="DATABASE")
    ap.add_argument("--no-schema", action="store_true")
    ap.add_argument("--prefix", default="deployment", help="Text placed before the date in the file name")
    ap.add_argument("--date", help="Date tag YYYYMMDD for the file name (default: today, UTC)")
    ap.add_argument("--connection", help="Connection name in connections.toml (default connection if omitted)")
    args = ap.parse_args()

    if args.date and not re.fullmatch(r"\d{8}", args.date):
        print("--date must be YYYYMMDD, for example 20261124", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[A-Za-z0-9_]*", args.prefix):
        print("--prefix may contain only letters, digits and underscores", file=sys.stderr)
        return 2

    if not os.path.isfile(args.list_file):
        print("List file not found: %s (nothing to do)" % args.list_file)
        return 0
    with open(args.list_file, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not any(l.strip() and not l.strip().startswith("#") for l in lines):
        print("No object names in %s (nothing to do)" % args.list_file)
        return 0

    import snowflake.connector
    conn = snowflake.connector.connect(connection_name=args.connection) if args.connection else snowflake.connector.connect()
    try:
        created, failed, kept = process(conn.cursor(), lines, args.repo_root, args.migrations_dir,
                                        args.bump, args.var_name, not args.no_schema,
                                        args.prefix, args.date)
    finally:
        conn.close()

    with open(args.list_file, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept).rstrip("\n") + "\n")
    print("Created %d file(s), %d failed." % (len(created), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
