"""Entry point for Atlas — Document Q&A. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["document-qa"] + sys.argv[1:])
