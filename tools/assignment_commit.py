#!/usr/bin/env python3
"""Commit wrapper that records AI-use metadata and quiz answers."""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT_MARKER = ".assignment"
METADATA_FILE = "commit-metadata.jsonl"


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ASSIGNMENT_COMMIT_WRAPPER"] = "1"
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def require_git_repo() -> None:
    result = run_git(["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        print("This command must be run inside a Git repository.", file=sys.stderr)
        sys.exit(2)
    os.chdir(result.stdout.strip())


def prompt(label: str, *, required: bool = True) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value or not required:
            return value
        print("This field is required.")


def prompt_multiline(label: str, *, required: bool = True) -> str:
    print(f"{label} (finish with a blank line):")
    lines: list[str] = []
    while True:
        line = input("> ")
        if line == "":
            break
        lines.append(line)
    value = "\n".join(lines).strip()
    if required and not value:
        print("This field is required.")
        return prompt_multiline(label, required=required)
    return value


def yes_no(label: str) -> bool:
    while True:
        value = input(f"{label} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def get_staged_files() -> list[str]:
    result = run_git(["diff", "--cached", "--name-only"])
    return [line for line in result.stdout.splitlines() if line.strip()]


def get_staged_summary() -> str:
    result = run_git(["diff", "--cached", "--stat"])
    return result.stdout.strip()


def get_staged_diff_name_status() -> list[dict[str, str]]:
    result = run_git(["diff", "--cached", "--name-status"])
    items: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            items.append({"status": parts[0], "path": parts[-1]})
    return items


def build_quiz(files: list[str]) -> list[str]:
    questions = [
        "Explain this commit in your own words.",
        "What is the most important behavior changed by this commit?",
        "What test or manual check proves this commit works?",
    ]
    if files:
        questions.append(f"Why did you change {files[0]}?")
    if len(files) > 1:
        questions.append(f"How do the changes in {files[0]} relate to {files[1]}?")
    questions.append("What could go wrong with this change?")
    return questions[:5]


def collect_metadata() -> dict[str, object]:
    files = get_staged_files()
    if not files:
        print("No staged changes found. Stage files with git add first.", file=sys.stderr)
        sys.exit(1)

    print("\nStaged change summary")
    print("---------------------")
    summary = get_staged_summary()
    print(summary or "\n".join(files))
    print()

    message = prompt("Commit message")
    ai_used = yes_no("Did you use AI help for this commit?")

    ai_metadata: dict[str, object] = {"ai_used": ai_used}
    if ai_used:
        ai_metadata["tool"] = prompt("AI tool used")
        ai_metadata["prompts"] = prompt_multiline("Paste the main prompt(s) used")
        ai_metadata["accepted_ai_suggestions"] = prompt_multiline(
            "What AI suggestions did you accept?"
        )
        ai_metadata["student_modifications"] = prompt_multiline(
            "What did you change yourself?"
        )
    else:
        ai_metadata["tool"] = "none"
        ai_metadata["prompts"] = ""
        ai_metadata["accepted_ai_suggestions"] = ""
        ai_metadata["student_modifications"] = prompt_multiline(
            "Briefly describe how you completed this without AI"
        )

    confidence = prompt(
        "Understanding level (fully understand / partly understand / do not understand)"
    )

    quiz_questions = build_quiz(files)
    quiz_answers = []
    print("\nCommit quiz")
    print("-----------")
    for index, question in enumerate(quiz_questions, start=1):
        answer = prompt_multiline(f"Q{index}. {question}")
        quiz_answers.append({"question": question, "answer": answer})

    return {
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "commit": None,
        "parent_commit": run_git(["rev-parse", "HEAD"], check=False).stdout.strip(),
        "commit_message": message,
        "files": get_staged_diff_name_status(),
        "ai": ai_metadata,
        "understanding_level": confidence,
        "quiz": quiz_answers,
    }


def ensure_assignment_dir() -> Path:
    path = Path(ROOT_MARKER)
    path.mkdir(exist_ok=True)
    return path


def append_metadata(record: dict[str, object]) -> None:
    path = ensure_assignment_dir() / METADATA_FILE
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def commit_with_metadata(record: dict[str, object]) -> str:
    message = str(record["commit_message"])
    trailer = "AI-Metadata: .assignment/commit-metadata.jsonl"
    full_message = f"{message}\n\n{trailer}\n"
    run_git(["commit", "-m", full_message])
    result = run_git(["rev-parse", "HEAD"])
    return result.stdout.strip()


def main() -> int:
    require_git_repo()
    record = collect_metadata()
    append_metadata(record)
    run_git(["add", f"{ROOT_MARKER}/{METADATA_FILE}"])
    commit_sha = commit_with_metadata(record)
    print(f"\nCommitted with AI metadata: {commit_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
