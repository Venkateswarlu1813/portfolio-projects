"""Entry point for Stockroom — Inventory Operations. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["inventory"] + sys.argv[1:])
