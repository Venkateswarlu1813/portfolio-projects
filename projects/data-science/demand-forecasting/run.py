"""Entry point for Daily Demand Forecasting. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["demand-forecasting"] + sys.argv[1:])
