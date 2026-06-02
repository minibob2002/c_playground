#!/usr/bin/env python3
"""Generate a teacher report for assignment AI metadata."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


METADATA_PATH = Path(".assignment") / "commit-metadata.jsonl"
REPORT_PATH = Path(".assignment") / "ai-metadata-grade-report.md"


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_git_repo() -> None:
    result = run_git(["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        print("This command must be run inside a Git repository.", file=sys.stderr)
        sys.exit(2)
    os.chdir(result.stdout.strip())


def commit_list() -> list[str]:
    has_start = run_git(["rev-parse", "--verify", "assignment-start"], check=False)
    if has_start.returncode == 0:
        result = run_git(["rev-list", "--reverse", "assignment-start..HEAD"])
    else:
        result = run_git(["rev-list", "--reverse", "HEAD"])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def commit_files(commit: str) -> list[str]:
    result = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", commit])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def short(commit: str) -> str:
    return commit[:7]


def load_metadata() -> list[dict[str, object]]:
    if not METADATA_PATH.exists():
        return []
    records = []
    for line_number, line in enumerate(METADATA_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "commit": None,
                    "parse_error": f"Line {line_number}: {exc}",
                    "raw": line,
                }
            )
    return records


def score_record(record: dict[str, object], files: list[str]) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []

    if record.get("parse_error"):
        return 0, [str(record["parse_error"])]

    ai = record.get("ai")
    quiz = record.get("quiz")
    understanding = str(record.get("understanding_level", "")).strip().lower()

    if isinstance(ai, dict):
        score += 20
        if ai.get("ai_used") is True:
            if str(ai.get("tool", "")).strip():
                score += 10
            else:
                notes.append("AI tool missing.")
            if str(ai.get("prompts", "")).strip():
                score += 20
            else:
                notes.append("AI prompt text missing despite AI use.")
            if str(ai.get("accepted_ai_suggestions", "")).strip():
                score += 10
            else:
                notes.append("Accepted AI suggestions missing.")
            if str(ai.get("student_modifications", "")).strip():
                score += 10
            else:
                notes.append("Student modifications missing.")
        elif ai.get("ai_used") is False:
            score += 30
            if str(ai.get("student_modifications", "")).strip():
                score += 10
            else:
                notes.append("Non-AI work explanation missing.")
        else:
            notes.append("AI-used field is unclear.")
    else:
        notes.append("AI metadata block missing.")

    if isinstance(quiz, list) and len(quiz) >= 3:
        answered = [
            item
            for item in quiz
            if isinstance(item, dict) and str(item.get("answer", "")).strip()
        ]
        if len(answered) >= 3:
            score += 20
        else:
            notes.append("Quiz has fewer than three answered questions.")
    else:
        notes.append("Quiz answers missing or too short.")

    text_blob = json.dumps(record, ensure_ascii=True).lower()
    if files and any(Path(file).name.lower() in text_blob for file in files):
        score += 10
    elif files:
        notes.append("Metadata does not mention any changed file names.")

    if "fully" in understanding:
        score += 10
    elif "partly" in understanding:
        score += 5
        notes.append("Student reports partial understanding.")
    elif understanding:
        notes.append(f"Student reports weak understanding: {understanding}.")
    else:
        notes.append("Understanding level missing.")

    return min(score, 100), notes


def build_report() -> str:
    commits = commit_list()
    records = load_metadata()
    by_commit = {
        str(record.get("commit")): record
        for record in records
        if record.get("commit") is not None
    }

    lines = [
        "# AI Metadata Grade Report",
        "",
        f"Commits inspected: {len(commits)}",
        f"Metadata records found: {len(records)}",
        "",
        "## Results",
        "",
        "| Commit | Score | Status | Notes |",
        "| --- | ---: | --- | --- |",
    ]

    scores: list[int] = []
    ordered_records = [record for record in records if not record.get("parse_error")]
    order_index = 0
    for index, commit in enumerate(commits):
        if index == 0 and run_git(["rev-parse", "--verify", "assignment-start"], check=False).returncode != 0:
            lines.append(f"| `{short(commit)}` | n/a | Initial commit | Not graded. |")
            continue
        record = by_commit.get(commit)
        if not record and order_index < len(ordered_records):
            record = ordered_records[order_index]
            order_index += 1
        if not record:
            lines.append(f"| `{short(commit)}` | 0 | Missing | No metadata record for this commit. |")
            scores.append(0)
            continue
        files = commit_files(commit)
        score, notes = score_record(record, files)
        scores.append(score)
        status = "Pass" if score >= 70 else "Review"
        note_text = " ".join(notes) if notes else "Complete enough for metadata review."
        lines.append(f"| `{short(commit)}` | {score} | {status} | {note_text} |")

    average = round(sum(scores) / len(scores), 1) if scores else 0
    lines.extend(
        [
            "",
            "## Suggested Metadata Grade",
            "",
            f"{average}/100",
            "",
            "This score evaluates disclosure and understanding evidence, not code correctness.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    require_git_repo()
    REPORT_PATH.parent.mkdir(exist_ok=True)
    report = build_report()
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
