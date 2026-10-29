"""Browser interface for three separate AI workflows; loopback demo by default."""
import argparse
import os
import secrets
from flask import Flask, render_template, request, session
from portfolio.genai import run, ProviderError, DATA

PROJECTS = {
    "document-qa": ("Atlas / Document Q&A", "Ask your handbook. Trace every answer.", "How long are backups retained?"),
    "support-drafts": ("ReplyDesk / Support Drafts", "Turn a customer request into a policy-grounded draft.", "Can I get a refund for my purchase?"),
    "meeting-actions": ("Minute / Meeting Actions", "Find explicit commitments with their original evidence.", (DATA / "meeting.txt").read_text(encoding="utf-8")),
}


def create_app(project, config=None):
    title, subtitle, example = PROJECTS[project]
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
                      MAX_CONTENT_LENGTH=40000, SESSION_COOKIE_NAME="portfolio_" + project.replace("-", "_"),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    if config:
        app.config.update(config)

    @app.after_request
    def headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.route("/", methods=["GET", "POST"])
    def index():
        session.setdefault("csrf", secrets.token_hex(24))
        result, error = None, None
        text = request.form.get("text", example)
        mode = request.form.get("mode", "offline")
        if request.method == "POST":
            if not secrets.compare_digest(session["csrf"], request.form.get("csrf", "")):
                return "Invalid form token", 400
            if len(text) > 30000:
                error = "Input is too long (maximum 30000 characters)."
            elif mode == "openai" and request.form.get("consent") != "yes":
                error = "Confirm sending this text and retrieved context to OpenAI."
            else:
                try:
                    result = run(project, text, mode)
                except (ValueError, ProviderError) as exc:
                    error = str(exc)
        return render_template("ai.html", title=title, subtitle=subtitle, text=text,
                               mode=mode, result=result, error=error, project=project)
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=list(PROJECTS))
    parser.add_argument("--port", type=int, default=5100)
    args = parser.parse_args()
    create_app(args.project).run(host="127.0.0.1", port=args.port)
