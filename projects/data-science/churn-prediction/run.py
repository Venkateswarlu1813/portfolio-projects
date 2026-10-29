"""Entry point for Customer Churn Prediction. Install the repository package first."""
import sys
from portfolio.__main__ import main

if __name__ == "__main__":
    main(["churn-prediction"] + sys.argv[1:])
