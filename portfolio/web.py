"""Three server-rendered applications with SQLite persistence and shared auth."""
import argparse
import csv
from datetime import date, timedelta
from functools import wraps
import io
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   Response, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

PROJECTS = {
    "job-tracker": {"title": "CareerBoard", "tagline": "Keep your next opportunity in focus.",
        "noun": "Application", "label": "Company", "detail": "Role", "extra": "Follow-up date",
        "states": ["Saved", "Applied", "Interview", "Offer", "Rejected"], "accent": "blue"},
    "inventory": {"title": "Stockroom", "tagline": "Know what is in stock. Track every movement.",
        "noun": "Product", "label": "Product name", "detail": "SKU", "extra": "Reorder level",
        "states": ["Active", "Discontinued"], "accent": "green"},
    "team-tasks": {"title": "TeamFlow", "tagline": "A shared view of what happens next.",
        "noun": "Task", "label": "Task title", "detail": "Description", "extra": "Due date",
        "states": ["Todo", "Doing", "Blocked", "Done"], "accent": "orange"},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workspaces (
 id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id), name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS members (
 workspace_id INTEGER REFERENCES workspaces(id), user_id INTEGER REFERENCES users(id),
 PRIMARY KEY(workspace_id,user_id));
CREATE TABLE IF NOT EXISTS records (
 id INTEGER PRIMARY KEY, workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
 label TEXT NOT NULL, detail TEXT NOT NULL, extra TEXT NOT NULL,
 state TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
 assignee_id INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(workspace_id,detail));
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, record_id INTEGER NOT NULL REFERENCES records(id),
 actor_id INTEGER NOT NULL REFERENCES users(id), action TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS movements (
 id INTEGER PRIMARY KEY, record_id INTEGER NOT NULL REFERENCES records(id),
 actor_id INTEGER NOT NULL REFERENCES users(id), delta INTEGER NOT NULL CHECK(delta!=0),
 reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS login_attempts (
 identity TEXT NOT NULL, attempted_at REAL NOT NULL);
"""


def create_app(project, config=None):
    settings = PROJECTS[project]
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / f"{project}.sqlite"),
        MAX_CONTENT_LENGTH=32000, SESSION_COOKIE_NAME="portfolio_" + project.replace("-", "_"), SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.executescript(SCHEMA)

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys=ON")
        return g.db

    @app.teardown_appcontext
    def close(_):
        if "db" in g:
            g.db.close()

    @app.before_request
    def guard():
        session.setdefault("csrf", secrets.token_hex(24))
        if request.method == "POST" and not secrets.compare_digest(session["csrf"], request.form.get("csrf", "")):
            abort(400, "Invalid form token; reload and try again")
        g.user = db().execute("SELECT id,username FROM users WHERE id=?", (session.get("user_id"),)).fetchone()

    @app.after_request
    def headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def context():
        return dict(settings=settings, project=project)

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapped

    def workspace():
        row = db().execute("SELECT w.* FROM workspaces w JOIN members m ON m.workspace_id=w.id "
            "WHERE w.id=? AND m.user_id=?", (session.get("workspace_id"), g.user["id"])).fetchone()
        if row is None:
            row = db().execute("SELECT w.* FROM workspaces w JOIN members m ON m.workspace_id=w.id "
                "WHERE m.user_id=? ORDER BY w.id LIMIT 1", (g.user["id"],)).fetchone()
        if row is None:
            abort(403)
        session["workspace_id"] = row["id"]
        return row

    def record(record_id):
        row = db().execute("SELECT * FROM records WHERE id=? AND workspace_id=?",
                           (record_id, workspace()["id"])).fetchone()
        if row is None:
            abort(404)
        return row

    def event(record_id, action):
        db().execute("INSERT INTO events(record_id,actor_id,action) VALUES(?,?,?)",
                     (record_id, g.user["id"], action))

    def field(name, maximum=160):
        value = request.form.get(name, "").strip()
        if not value or len(value) > maximum:
            raise ValueError(f"{name} must contain 1 to {maximum} characters")
        return value

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            try:
                name = field("username", 40).lower()
                password = field("password", 200)
                if not re.fullmatch(r"[a-z0-9_.-]{3,40}", name) or len(password) < 12:
                    raise ValueError("Use a 3–40 character username and a password of at least 12 characters")
                with db():
                    user = db().execute("INSERT INTO users(username,password) VALUES(?,?)",
                        (name, generate_password_hash(password))).lastrowid
                    wid = db().execute("INSERT INTO workspaces(owner_id,name) VALUES(?,?)",
                        (user, name + "'s workspace")).lastrowid
                    db().execute("INSERT INTO members VALUES(?,?)", (wid, user))
                session.clear()
                session.update(user_id=user, workspace_id=wid, csrf=secrets.token_hex(24))
                session.permanent = True
                return redirect(url_for("index"))
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(str(exc) if isinstance(exc, ValueError) else "Username is already registered", "error")
        return render_template("auth.html", action="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            identity = request.form.get("username", "").strip().lower()
            now = time.time()
            with db():
                db().execute("DELETE FROM login_attempts WHERE attempted_at<?", (now-900,))
            count = db().execute("SELECT COUNT(*) FROM login_attempts WHERE identity=?", (identity,)).fetchone()[0]
            if count >= 5:
                return render_template("error.html", message="Too many attempts. Try again in 15 minutes."), 429
            user = db().execute("SELECT * FROM users WHERE username=?", (identity,)).fetchone()
            password = request.form.get("password", "")
            if len(password) <= 200 and user and check_password_hash(user["password"], password):
                with db():
                    db().execute("DELETE FROM login_attempts WHERE identity=?", (identity,))
                session.clear()
                session.update(user_id=user["id"], csrf=secrets.token_hex(24))
                session.permanent = True
                return redirect(url_for("index"))
            with db():
                db().execute("INSERT INTO login_attempts VALUES(?,?)", (identity, now))
            flash("Username or password is incorrect", "error")
        return render_template("auth.html", action="login")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        ws = workspace()
        q = request.args.get("q", "")[:100]
        state = request.args.get("state", "")
        rows = db().execute("SELECT r.*,u.username AS assignee FROM records r LEFT JOIN users u "
            "ON u.id=r.assignee_id WHERE r.workspace_id=? AND (r.label LIKE ? OR r.detail LIKE ?) "
            "AND (?='' OR r.state=?) ORDER BY r.id DESC",
            (ws["id"], "%"+q+"%", "%"+q+"%", state, state)).fetchall()
        all_rows = db().execute("SELECT * FROM records WHERE workspace_id=?", (ws["id"],)).fetchall()
        counts = {s: sum(r["state"] == s for r in all_rows) for s in settings["states"]}
        low = sum(r["quantity"] <= int(r["extra"]) for r in all_rows if r["state"] == "Active") if project == "inventory" else 0
        due = sum(bool(r["extra"]) and r["extra"] <= str(date.today()) and r["state"] not in ["Done", "Offer", "Rejected"] for r in all_rows) if project != "inventory" else 0
        members = db().execute("SELECT u.id,u.username FROM users u JOIN members m ON m.user_id=u.id "
            "WHERE m.workspace_id=?", (ws["id"],)).fetchall()
        spaces = db().execute("SELECT w.* FROM workspaces w JOIN members m ON m.workspace_id=w.id "
            "WHERE m.user_id=?", (g.user["id"],)).fetchall()
        return render_template("dashboard.html", rows=rows, counts=counts, total=len(all_rows),
            low=low, due=due, q=q, state=state, ws=ws, members=members, spaces=spaces)

    @app.post("/records")
    @login_required
    def create_record():
        ws = workspace()
        try:
            label, detail = field("label"), field("detail", 1000)
            extra = request.form.get("extra", "").strip()
            if project == "inventory":
                level = int(extra)
                if not 0 <= level <= 1000000:
                    raise ValueError("Reorder level must be between 0 and 1000000")
                extra = str(level)
            elif extra:
                extra = date.fromisoformat(extra).isoformat()
            assignee = None
            if project == "team-tasks" and request.form.get("assignee"):
                assignee = int(request.form["assignee"])
                if not db().execute("SELECT 1 FROM members WHERE workspace_id=? AND user_id=?", (ws["id"], assignee)).fetchone():
                    raise ValueError("Assignee must belong to the workspace")
            with db():
                rid = db().execute("INSERT INTO records(workspace_id,label,detail,extra,state,assignee_id) VALUES(?,?,?,?,?,?)",
                    (ws["id"], label, detail, extra, settings["states"][0], assignee)).lastrowid
                event(rid, "Created")
            flash(settings["noun"] + " added", "success")
        except (ValueError, sqlite3.IntegrityError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "This SKU, role, or description already exists in this workspace", "error")
        return redirect(url_for("index"))

    @app.post("/records/<int:record_id>/state")
    @login_required
    def change_state(record_id):
        row = record(record_id)
        state = request.form.get("state", "")
        if state not in settings["states"]:
            abort(400, "Unknown status")
        if project == "job-tracker":
            allowed = {"Saved": ["Applied", "Rejected"], "Applied": ["Interview", "Rejected"],
                       "Interview": ["Offer", "Rejected"], "Offer": [], "Rejected": ["Saved"]}
            if state != row["state"] and state not in allowed[row["state"]]:
                flash("That stage transition is not allowed", "error")
                return redirect(url_for("index"))
        with db():
            db().execute("UPDATE records SET state=? WHERE id=?", (state, record_id))
            event(record_id, row["state"] + " → " + state)
        return redirect(url_for("index"))

    @app.post("/records/<int:record_id>/stock")
    @login_required
    def stock(record_id):
        if project != "inventory":
            abort(404)
        row = record(record_id)
        if row["state"] != "Active":
            abort(400, "Reactivate this product before recording stock")
        try:
            delta = int(request.form.get("delta", ""))
            reason = field("reason", 250)
            if delta == 0 or abs(delta) > 1000000:
                raise ValueError("Movement must be nonzero and no more than 1000000 units")
            with db():
                changed = db().execute("UPDATE records SET quantity=quantity+? WHERE id=? AND quantity+? >= 0",
                                       (delta, record_id, delta)).rowcount
                if not changed:
                    raise ValueError("Insufficient stock; movement was not recorded")
                db().execute("INSERT INTO movements(record_id,actor_id,delta,reason) VALUES(?,?,?,?)",
                             (record_id, g.user["id"], delta, reason))
                event(record_id, f"Stock {delta:+d}: {reason}")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("index"))

    @app.get("/records/<int:record_id>")
    @login_required
    def history(record_id):
        row = record(record_id)
        events = db().execute("SELECT e.*,u.username FROM events e JOIN users u ON u.id=e.actor_id "
            "WHERE record_id=? ORDER BY e.id DESC", (record_id,)).fetchall()
        return render_template("history.html", row=row, events=events)

    @app.post("/workspace")
    @login_required
    def switch_workspace():
        wid = request.form.get("workspace_id", "")
        if not db().execute("SELECT 1 FROM members WHERE workspace_id=? AND user_id=?", (wid, g.user["id"])).fetchone():
            abort(403)
        session["workspace_id"] = int(wid)
        return redirect(url_for("index"))

    @app.post("/members")
    @login_required
    def add_member():
        if project != "team-tasks":
            abort(404)
        ws = workspace()
        if ws["owner_id"] != g.user["id"]:
            abort(403)
        username = request.form.get("username", "").strip().lower()
        user = db().execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if user is None:
            flash("Ask your teammate to register here first", "error")
        else:
            with db():
                db().execute("INSERT OR IGNORE INTO members VALUES(?,?)", (ws["id"], user["id"]))
            flash("Member added to this workspace", "success")
        return redirect(url_for("index"))

    @app.get("/export.csv")
    @login_required
    def export():
        rows = db().execute("SELECT label,detail,extra,state,quantity FROM records WHERE workspace_id=?",
                            (workspace()["id"],)).fetchall()
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["label", "detail", "extra", "state", "quantity"])
        for row in rows:
            writer.writerow(["'"+str(v) if str(v).lstrip().startswith(("=", "+", "-", "@")) else v for v in row])
        return Response(stream.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={project}.csv"})

    @app.get("/health")
    def health():
        db().execute("SELECT 1").fetchone()
        return {"status": "ok", "project": project}

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(exc):
        return render_template("error.html", message=exc.description), exc.code

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=list(PROJECTS))
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    create_app(args.project).run(host="127.0.0.1", port=args.port)
