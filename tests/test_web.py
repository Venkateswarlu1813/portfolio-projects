import sqlite3
import pytest
from portfolio.web import create_app


def post(client, path, **fields):
    with client.session_transaction() as session:
        csrf = session["csrf"]
    return client.post(path, data=dict(csrf=csrf, **fields), follow_redirects=True)


def register(client, username="alice"):
    client.get("/register")
    return post(client, "/register", username=username, password="demo-password-long")


@pytest.fixture(params=["job-tracker", "inventory", "team-tasks"])
def app(request, tmp_path):
    return create_app(request.param, {"TESTING": True, "SECRET_KEY": "test-only-secret", "DATABASE": str(tmp_path / "test.sqlite")})


def test_registration_login_persistence_and_isolation(app):
    alice = app.test_client()
    assert register(alice).status_code == 200
    extra = "5" if "inventory" in app.config["DATABASE"] else ""
    # Detect inventory through health rather than storage path.
    kind = alice.get("/health").json["project"]
    extra = "5" if kind == "inventory" else "2026-11-01"
    response = post(alice, "/records", label="Example", detail="Unique description", extra=extra)
    assert b"Example" in response.data
    assert b"Created" in alice.get("/records/1").data
    bob = app.test_client()
    register(bob, "bob")
    assert b"Unique description" not in bob.get("/").data
    assert bob.get("/records/1").status_code == 404
    assert post(bob, "/records/1/state", state="Done").status_code == 404
    assert post(bob, "/workspace", workspace_id="1").status_code == 403
    post(alice, "/logout")
    response = post(alice, "/login", username="alice", password="demo-password-long")
    assert b"Example" in response.data
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        stored = conn.execute("SELECT password FROM users WHERE username='alice'").fetchone()[0]
        assert stored != "demo-password-long"


def test_csrf_xss_export_and_search(app):
    client = app.test_client()
    register(client)
    assert client.post("/records", data={"label": "x"}).status_code == 400
    project = client.get("/health").json["project"]
    response = post(client, "/records", label="<script>alert(1)</script>", detail="=SUM(A1:A2)",
                    extra="5" if project == "inventory" else "2026-11-01")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert b"'=SUM" in client.get("/export.csv").data
    assert b"No matching records" in client.get("/?q=nomatch123").data
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_login_rate_limit(app):
    client = app.test_client()
    register(client)
    post(client, "/logout")
    for _ in range(5):
        assert post(client, "/login", username="alice", password="incorrect").status_code == 200
    assert post(client, "/login", username="alice", password="incorrect").status_code == 429


def test_inventory_atomic_stock_and_ledger(tmp_path):
    app = create_app("inventory", {"TESTING": True, "DATABASE": str(tmp_path / "stock.sqlite")})
    client = app.test_client()
    register(client)
    post(client, "/records", label="Notebook", detail="NOTE-01", extra="5")
    post(client, "/records/1/stock", delta="10", reason="Opening delivery")
    post(client, "/records/1/stock", delta="-3", reason="Customer order")
    assert b"Insufficient stock" in post(client, "/records/1/stock", delta="-20", reason="Invalid").data
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        assert conn.execute("SELECT quantity FROM records").fetchone()[0] == 7
        assert conn.execute("SELECT SUM(delta) FROM movements").fetchone()[0] == 7
        assert conn.execute("SELECT COUNT(*) FROM movements").fetchone()[0] == 2


def test_job_stage_transitions(tmp_path):
    app = create_app("job-tracker", {"TESTING": True, "DATABASE": str(tmp_path / "jobs.sqlite")})
    client = app.test_client()
    register(client)
    post(client, "/records", label="Fictional Labs", detail="Python developer", extra="2026-11-01")
    assert b"not allowed" in post(client, "/records/1/state", state="Offer").data
    for state in ["Applied", "Interview", "Offer"]:
        assert post(client, "/records/1/state", state=state).status_code == 200
    assert b"Interview" in client.get("/records/1").data


def test_team_membership_assignment_and_owner_permission(tmp_path):
    app = create_app("team-tasks", {"TESTING": True, "DATABASE": str(tmp_path / "tasks.sqlite")})
    owner, member, outsider = [app.test_client() for _ in range(3)]
    register(owner, "owner")
    register(member, "member")
    register(outsider, "outsider")
    post(owner, "/members", username="member")
    post(member, "/workspace", workspace_id="1")
    assert post(member, "/members", username="outsider").status_code == 403
    assert b"must belong" in post(owner, "/records", label="Invalid task", detail="Hidden member", extra="", assignee="3").data
    post(owner, "/records", label="Ship dashboard", detail="Review responsive states", extra="2026-11-01", assignee="2")
    assert b"Ship dashboard" in member.get("/").data
    assert b"Ship dashboard" not in outsider.get("/").data
    post(member, "/records/1/state", state="Done")
    assert b"member" in owner.get("/records/1").data


def test_apps_use_distinct_session_cookie_names(tmp_path):
    from portfolio.ai_web import create_app as ai_app
    names = [create_app(project, {"TESTING": True, "DATABASE": str(tmp_path / (project + '.sqlite'))}).config['SESSION_COOKIE_NAME']
             for project in ['job-tracker', 'inventory', 'team-tasks']]
    names += [ai_app(project, {"TESTING": True}).config['SESSION_COOKIE_NAME']
              for project in ['document-qa', 'support-drafts', 'meeting-actions']]
    assert len(set(names)) == 6
