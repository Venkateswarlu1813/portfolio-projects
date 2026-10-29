"""Entry point for CareerBoard — Job Application Tracker. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["job-tracker"] + sys.argv[1:])
