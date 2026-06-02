# Assignment AI Metadata Kit

This kit helps a teacher require per-commit AI-use disclosure and quiz evidence.

## Student Workflow

Students should work in their fork and commit with:

```powershell
python tools/assignment_commit.py
```

The command:

1. Checks the staged Git diff.
2. Asks whether AI was used.
3. Captures tool name, prompts, accepted suggestions, student changes, and confidence.
4. Generates a small commit-specific quiz from the changed files.
5. Saves metadata to `.assignment/commit-metadata.jsonl`.
6. Creates the Git commit.

The metadata file is committed together with the code change. Because a Git commit
cannot contain its own final SHA without changing that SHA, the grader maps records
to commits by chronological order.

Students can stage files normally:

```powershell
git add .
python tools/assignment_commit.py
```

Give students `ASSIGNMENT_AI_POLICY.md` in the repository root so the rule is visible before they start coding.

## Optional Git Hook

Teachers can ask students to install the helper hook:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_assignment_hook.ps1
```

The hook blocks direct `git commit` and tells students to use:

```powershell
python tools/assignment_commit.py
```

Git hooks are useful reminders, but they are not tamper-proof. Students can bypass them, so grading should also inspect commit metadata.

## Teacher Workflow

When the public template repository is ready, mark the starting point:

```powershell
git tag assignment-start
git push origin assignment-start
```

After students submit a GitHub fork link in the LMS, clone the fork and run:

```powershell
python tools/grade_ai_metadata.py
```

The grader checks:

- commits after the initial commit
- whether each commit has metadata
- whether AI-use fields are complete
- whether prompt text is present when AI use is disclosed
- whether quiz answers exist
- whether the student's explanation mentions files touched by the commit

The output is a Markdown report at:

```text
.assignment/ai-metadata-grade-report.md
```

For public GitHub repositories, copy `.github/workflows/ai-metadata-check.yml` into the assignment repository. It publishes the metadata report as a workflow artifact on every push.

## Important Limitation

This kit cannot prove that every external AI prompt was captured. It creates an auditable disclosure and understanding trail. Stronger capture requires a controlled coding environment or approved agent interface.
