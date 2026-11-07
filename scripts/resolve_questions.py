"""Executable SYNTHETIC tutorial: four tasks, attached bytes, QA approval, reassessment.

Only contacts the local loopback demo. Never logs role keys. Requires a fresh questions case.
"""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

from workbench.demo import example_document


def resolve_questions(runtime, port):
    keys = json.loads((Path(runtime) / "credentials.json").read_text())
    base = f"http://127.0.0.1:{port}/api"

    def call(path, method="GET", data=None, role="harbor-qa"):
        request = Request(
            base + path,
            method=method,
            headers={"Authorization": "Bearer " + keys[role], "Content-Type": "application/json"},
            data=json.dumps(data).encode() if data is not None else None,
        )
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    path = "/cases/DEMO-QUESTIONS"
    evaluations = call(path + "/evaluations")
    original = evaluations[0]
    steps = [
        ("study", "STUDY_APPLICABILITY"),
        ("sop", "SOP_AUTHORITY"),
        ("exposure", "EXPOSURE_RELATIONSHIP"),
        ("history", "BATCH_HISTORY"),
    ]
    if {task["reason_code"] for task in evaluations[-1]["result"]["tasks"]} != {
        reason for _, reason in steps
    }:
        raise ValueError("Use a fresh synthetic questions case; this example is not a retry tool")
    payload = call(path)["input"]
    completions = []
    for kind, reason in steps:
        document = example_document(payload, kind, row=100)
        if kind == "sop":
            document["supersedes"] = [
                d["id"] for d in call(path + "/documents") if d["kind"] == "sop" and d["approved"]
            ]
        attached = call(path + "/documents", "POST", document, "harbor-operator")
        call(path + f"/documents/{attached['id']}/approval", "POST")
        completed = call(
            path + "/resolutions",
            "POST",
            {"bundle_id": original["id"], "reason_code": reason, "document_id": attached["id"]},
        )
        completions.append({"reason": reason, **completed})
    return {
        "synthetic": True,
        "completed": sum(item["status"] == "COMPLETE" for item in completions),
        "resolutions": completions,
        "original_tasks": len(call(f"/bundles/{original['id']}")["result"]["tasks"]),
        "current_result": call(path + "/evaluations")[-1]["result"]["recommendation"],
        "pending_obligations": len(call("/obligations")),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Resolve four SYNTHETIC local demo tasks; sends no external messages"
    )
    parser.add_argument("--runtime", type=Path, default=Path(".runtime"))
    parser.add_argument("--port", type=int, default=8174)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    print(json.dumps(resolve_questions(args.runtime, args.port), indent=2))


if __name__ == "__main__":
    main()
