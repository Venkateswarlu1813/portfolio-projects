"""One entry point, nine project workflows."""
import argparse
import json
from pathlib import Path

DATA_PROJECTS = {"churn-prediction": "churn", "demand-forecasting": "demand", "customer-segmentation": "segments"}
AI_PROJECTS = ["document-qa", "support-drafts", "meeting-actions"]
WEB_PROJECTS = ["job-tracker", "inventory", "team-tasks"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=list(DATA_PROJECTS) + AI_PROJECTS + WEB_PROJECTS)
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--csv", help="Optional data science input CSV")
    parser.add_argument("--snapshot", default="2026-01-01")
    parser.add_argument("--output", default="reports")
    parser.add_argument("--text", help="Run an AI project once in the terminal instead of starting its UI")
    parser.add_argument("--mode", choices=["offline", "openai"], default="offline")
    args = parser.parse_args(argv)
    if args.project in DATA_PROJECTS:
        from portfolio.data_science import run
        run(DATA_PROJECTS[args.project], args.output, args.csv, args.snapshot)
    elif args.project in AI_PROJECTS:
        if args.text is not None:
            from portfolio.genai import run
            print(json.dumps(run(args.project, args.text, args.mode), indent=2))
        else:
            from portfolio.ai_web import create_app
            create_app(args.project).run(host="127.0.0.1", port=args.port)
    else:
        from portfolio.web import create_app
        create_app(args.project).run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
