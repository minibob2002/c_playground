# AI Use And Commit Metadata Policy

For this assignment, every meaningful commit must include AI-use metadata.

You may use AI tools if the assignment permits it, but you must disclose them honestly. The goal is not only to record prompts. The goal is to show that you understand the code you submit.

## Required For Each Commit

Use:

```powershell
python tools/assignment_commit.py
```

For every commit, you will answer:

- whether AI was used
- which AI tool was used
- the main prompt or prompts
- which AI suggestions you accepted
- what you changed yourself
- a short quiz about the commit
- your understanding level

## Submission

Submit your public GitHub fork link in the LMS.

Before submitting, run:

```powershell
python tools/grade_ai_metadata.py
```

Review `.assignment/ai-metadata-grade-report.md` and fix any missing metadata before final submission.

## Academic Integrity

Missing, false, or obviously unrelated AI metadata may reduce the metadata score. Code correctness is graded separately from AI disclosure and understanding evidence.
