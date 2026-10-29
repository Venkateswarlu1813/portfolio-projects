"""Entry point for ReplyDesk — Policy-grounded Support Drafts. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["support-drafts"] + sys.argv[1:])
