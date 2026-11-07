"""Actual loopback HTTP + process restart; independent from ASGI TestClient.

Run from repository root: uv run --locked python -m scripts.smoke
Never logs generated credentials. Uses a disposable synthetic runtime.
"""

import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from workbench.demo import bootstrap


def run():
    with tempfile.TemporaryDirectory(prefix="evidence-smoke-") as directory:
        runtime = Path(directory) / "runtime"
        bootstrap(runtime)
        creds = json.loads((runtime / "credentials.json").read_text())
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        base = f"http://127.0.0.1:{port}"

        def request(path, method="GET", data=None, role="harbor-qa"):
            headers = {"Content-Type": "application/json"}
            if role:
                headers["Authorization"] = "Bearer " + creds[role]
            req = Request(
                base + path,
                method=method,
                headers=headers,
                data=json.dumps(data).encode() if data else None,
            )
            with urlopen(req, timeout=4) as response:
                return json.load(response)

        def start():
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "workbench",
                    "serve",
                    "--runtime",
                    str(runtime),
                    "--port",
                    str(port),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("server exited at startup")
                    try:
                        if request("/healthz", role=None)["status"] == "alive":
                            return process
                    except (URLError, TimeoutError):
                        time.sleep(0.05)
                raise RuntimeError("startup exceeded 10 seconds")
            except BaseException:
                process.terminate()
                process.wait(timeout=5)
                raise

        process = start()
        try:
            try:
                request("/api/cases", role=None)
                raise AssertionError("unauthenticated request accepted")
            except HTTPError as e:
                assert e.code == 401
            assert len(request("/api/cases")) == 3
            b = request("/api/cases/DEMO-READY/evaluations", "POST")
            assert b["result"]["recommendation"] == "WITHIN_SYNTHETIC_POLICY"
            ack = request(
                "/api/cases/DEMO-READY/acknowledgements",
                "POST",
                {
                    "bundle_id": b["id"],
                    "expected_hash": b["hash"],
                    "signer_label": "synthetic smoke review",
                    "outcome": "REVIEW_ACCEPTED",
                    "idempotency_key": "socket-smoke",
                },
            )
            assert ack["actor"] == "harbor-qa"
            before = request("/api/obligations")
            assert len(before) == 3 and before[0]["case_id"] == "DEMO-QUESTIONS"
        finally:
            process.terminate()
            process.wait(timeout=5)
        process = start()
        try:
            assert request("/api/obligations") == before
            assert request(f"/api/bundles/{b['id']}/replay")["matches"]
            assert request("/api/cases", role="meadow-reader") == []
        finally:
            process.terminate()
            process.wait(timeout=5)
        print(
            "PASS: real HTTP auth, 3 synthetic cases, evidence evaluation, local QA acknowledgement, independent deadlines, process restart, captured replay, cross-tenant denial"
        )


if __name__ == "__main__":
    run()
