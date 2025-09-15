#!/usr/bin/env python3
"""Restore all .bak files by replacing originals.
Creates a report of restored files.
"""
from __future__ import annotations
import glob
import os
import sys

files = glob.glob("**/*.bak", recursive=True)
if not files:
    print("No .bak files found")
    sys.exit(0)
count = 0
for f in files:
    orig = f[:-4]
    try:
        # overwrite if exists
        if os.path.exists(orig):
            os.remove(orig)
        os.replace(f, orig)
        print("restored", orig)
        count += 1
    except Exception as e:
        print("failed", f, e)
        sys.exit(1)
print("done", count)
