"""Use: uv run --locked python -m workbench demo"""

import argparse
import json
from pathlib import Path

from workbench.demo import backup, bootstrap


def main():
    parser = argparse.ArgumentParser(
        description="SYNTHETIC local evidence workbench; not a regulated system"
    )
    parser.add_argument("command", choices=["demo", "seed", "serve", "credential", "backup"])
    parser.add_argument(
        "name", nargs="?", default="harbor-qa", help="credential role, or backup target"
    )
    parser.add_argument("--runtime", type=Path, default=Path(".runtime"))
    parser.add_argument("--port", type=int, default=8174)
    args = parser.parse_args()
    if args.command in {"seed", "demo"}:
        if not args.runtime.exists():
            print(json.dumps(bootstrap(args.runtime)))
        elif args.command == "seed":
            parser.error("runtime already exists; use a new --runtime directory")
    if args.command == "credential":
        # Intentional local-only display; never printed during server start or logged by API.
        print(json.loads((args.runtime / "credentials.json").read_text())[args.name])
    elif args.command == "backup":
        print(json.dumps(backup(args.runtime / "workbench.db", Path(args.name))))
    elif args.command in {"demo", "serve"}:
        if not (args.runtime / "workbench.db").exists():
            parser.error("seed a runtime first")
        import uvicorn

        from workbench.api import create_app

        print(f"Open http://127.0.0.1:{args.port} — SYNTHETIC ONLY")
        print(
            "Login credential: run credential command in another terminal (never put tokens in URLs)."
        )
        uvicorn.run(
            create_app(args.runtime / "workbench.db"),
            host="127.0.0.1",
            port=args.port,
            access_log=False,
            limit_concurrency=50,
            timeout_keep_alive=5,
        )


if __name__ == "__main__":
    main()
