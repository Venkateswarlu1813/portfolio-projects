"""Entry point for TeamFlow — Workspace Task Management. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["team-tasks"] + sys.argv[1:])
