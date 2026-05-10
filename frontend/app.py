import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

API_URL = os.getenv("API_URL", "http://api:8080")

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node Registry Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .status { padding: 10px 16px; border-radius: 6px; margin-bottom: 20px; display: inline-block; font-weight: bold; }
        .status.ok { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
        th { background: #343a40; color: white; padding: 12px 16px; text-align: left; }
        td { padding: 10px 16px; border-bottom: 1px solid #dee2e6; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: #f8f9fa; }
        .btn { padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .form-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); margin-top: 24px; }
        .form-section h2 { margin-top: 0; color: #333; }
        .form-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
        .form-group { display: flex; flex-direction: column; gap: 4px; }
        .form-group label { font-size: 13px; color: #555; font-weight: bold; }
        .form-group input { padding: 8px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; }
        .error-msg { color: #dc3545; margin-bottom: 12px; font-weight: bold; }
        .health-section { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Node Registry Dashboard</h1>

    <div class="health-section">
        {% if health %}
            <div class="status ok">
                ✅ API Status: <strong>{{ health.status }}</strong> &nbsp;|&nbsp;
                DB: <strong>{{ health.db }}</strong> &nbsp;|&nbsp;
                active nodes: <strong>{{ health.nodes_count }}</strong>
            </div>
        {% else %}
            <div class="status error">❌ API Status: unreachable — active nodes unknown</div>
        {% endif %}
    </div>

    {% if error %}
        <div class="error-msg">Error: {{ error }}</div>
    {% endif %}

    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Host</th>
                <th>Port</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for node in nodes %}
            <tr>
                <td>{{ node.name }}</td>
                <td>{{ node.host }}</td>
                <td>{{ node.port }}</td>
                <td>{{ node.status }}</td>
                <td>
                    <form method="POST" action="/delete/{{ node.name }}" style="margin:0;">
                        <button type="submit" class="btn btn-danger">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center; color:#888;">No nodes registered.</td></tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="form-section">
        <h2>Register Node</h2>
        <form method="POST" action="/register">
            <div class="form-row">
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" id="name" name="name" placeholder="node-1" required>
                </div>
                <div class="form-group">
                    <label for="host">Host</label>
                    <input type="text" id="host" name="host" placeholder="192.168.1.1" required>
                </div>
                <div class="form-group">
                    <label for="port">Port</label>
                    <input type="number" id="port" name="port" placeholder="8080" min="1" max="65535" required>
                </div>
                <div class="form-group">
                    <button type="submit" class="btn btn-primary">Register</button>
                </div>
            </div>
        </form>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    health = None
    nodes = []
    error = request.args.get("error")

    try:
        h = requests.get(f"{API_URL}/health", timeout=5)
        health = h.json()
    except Exception:
        health = None

    try:
        r = requests.get(f"{API_URL}/api/nodes", timeout=5)
        nodes = r.json()
    except Exception:
        nodes = []

    return render_template_string(TEMPLATE, health=health, nodes=nodes, error=error)


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port = request.form.get("port", "").strip()

    try:
        payload = {"name": name, "host": host, "port": int(port)}
        r = requests.post(f"{API_URL}/api/nodes", json=payload, timeout=5)
        if r.status_code not in (200, 201):
            detail = r.json().get("detail", "Registration failed")
            return redirect(url_for("index", error=detail))
    except Exception as e:
        return redirect(url_for("index", error=str(e)))

    return redirect(url_for("index"))


@app.route("/delete/<name>", methods=["POST"])
def delete(name):
    try:
        requests.delete(f"{API_URL}/api/nodes/{name}", timeout=5)
    except Exception:
        pass
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)
