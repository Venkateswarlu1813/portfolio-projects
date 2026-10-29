# TeamFlow — Workspace Task Management

Collaborate on tasks with workspace membership, assignment, progress, and history.

## Run and walkthrough
`python -m portfolio team-tasks --port 5002`

Open http://127.0.0.1:5002. Register **owner** and, in a separate browser profile or after signing out, register **teammate**. Sign in as owner and use **Add registered teammate**. Create **Ship dashboard** with a due date and assign it to teammate. Sign in as teammate, switch to the owner's workspace, and move the task Todo → Doing → Done. Open history to see who made the change. A third account outside the workspace cannot view or update its tasks.

## Implementation
Flask HTML forms and a dedicated SQLite database. Each account gets a workspace; membership is checked on every lookup and write. Owners alone can add registered users. Members can create and update tasks and assign them only to workspace members. The owner explicitly grants access by adding a teammate; there is no email or background invitation flow. Dashboard counts, due dates, search, filters, and CSV export are included.

## Scope
Local demonstration. No deletion, arbitrary editing, notifications, attachments, or acceptance-based invites. Adding a registered username immediately grants that user membership. Duplicate task descriptions within a workspace are rejected by the shared schema. Extend with invitations, task-specific permissions, task editing with optimistic locking, comments, and recurring due dates.

## Shared setup and tests
Install from the repository root with `python -m pip install -e ".[dev]"`. Run all checks with `python -m pytest -q`. See the root README for environment setup, limitations, and code map.
