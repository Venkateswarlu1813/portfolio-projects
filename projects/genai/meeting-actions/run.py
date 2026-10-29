"""Entry point for Minute — Evidence-backed Meeting Actions. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["meeting-actions"] + sys.argv[1:])
