"""Entry point for RFM Customer Segmentation. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["customer-segmentation"] + sys.argv[1:])
