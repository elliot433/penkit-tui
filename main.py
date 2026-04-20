#!/usr/bin/env python3
import sys
import os

# Ensure project root is on sys.path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import PenKitApp
from core.config import load, ensure_output_dir


def main():
    cfg = load()
    ensure_output_dir(cfg)
    app = PenKitApp()
    app.run()


if __name__ == "__main__":
    main()
