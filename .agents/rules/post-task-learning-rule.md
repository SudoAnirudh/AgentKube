---
trigger: always_on
---


# Development Task Learning Documentation Rule

After completing **every development task**, STOP before moving to the next task and teach me what was done.

The goal is not just to make the code work. The goal is for me to **understand the system well enough to build and modify it myself**.

## Mandatory Documentation Requirement

After every completed task:

1. Create a **Markdown (`.md`) learning document** for that task.
2. Store all task explanations inside this Markdown file.
3. The Markdown file must contain the complete explanation described below.
4. Do not move to the next development task until the documentation is complete.
5. The documentation must be written in a technically accurate but beginner-friendly manner.
6. The documentation should reference the **actual files, modules, classes, and functions** changed during the task.
7. Do not create fake or hypothetical implementation details.

---

# Learning Document Structure

Every task documentation file must contain the following sections.

## 1. What Happened

Explain:

* What did we build, change, or fix?
* What is the final result?
* How does this task fit into the overall project?

Start with a simple explanation before going into technical details.

---

## 2. Why It Was Done

Explain:

* Why did we need this change?
* What problem does it solve?
* Why did we choose this approach?
* What alternatives could have been used?
* Why is the chosen approach appropriate?

Focus on the reasoning behind the implementation.

---

## 3. How It Works

Explain the complete execution flow from beginning to end.

Show how:

* Input enters the system.
* Modules process the input.
* Data moves between modules.
* External services or AI models are called.
* Results are produced and stored/returned.

Use diagrams when useful:

```text
Input
  ↓
Module A
  ↓
Module B
  ↓
Processing
  ↓
Output
```

---

## 4. Files and Modules

Create a table for important files:

| File | Purpose | What Changed | Connected To |
| ---- | ------- | ------------ | ------------ |

For each important file explain:

* Why the file exists.
* Its responsibility.
* Important code inside it.
* Which modules use it.
* Which modules it depends on.
* How it fits into the architecture.

---

## 5. Code Explanation

Explain the important:

* Classes
* Functions
* Methods
* Algorithms
* Logic
* APIs
* Data structures
* Configuration

Do **not** blindly explain every line.

Focus on code that is important for understanding the system.

For each important piece explain:

### What

What does this code do?

### Why

Why does this code exist?

### How

How does it work internally?

### Example

Give a simple example of how it behaves.

---

## 6. Two Levels of Explanation

Every difficult concept should be explained at two levels.

### Simple Explanation

Explain it as if I am learning the concept for the first time.

Use simple language and analogies where useful.

### Technical Explanation

Explain the actual engineering concept, implementation, and architecture.

Do not sacrifice technical accuracy for simplicity.

---

## 7. Practical Example

Always provide at least one realistic example.

The example must be connected to the **actual implementation**.

For example:

```text
User sends request
       ↓
API receives request
       ↓
Task is created
       ↓
Worker processes task
       ↓
AI model generates result
       ↓
Result is stored
       ↓
User receives response
```

Explain what happens at every step and identify the actual files/functions responsible.

---

## 8. Technical Concepts Learned

Identify new concepts introduced by the task.

For every important concept explain:

### What is it?

Simple definition.

### Why do we use it?

Its purpose in this project.

### How does it work?

Technical explanation.

### Where is it used?

Reference the actual file/module/function.

---

## 9. Errors and Edge Cases

Explain:

* What can go wrong?
* What happens with invalid input?
* What happens when dependencies fail?
* What happens when an API fails?
* What happens when an AI model fails?
* What happens when multiple requests arrive?
* What happens if the process crashes?

Clearly classify each relevant case:

* ✅ **Implemented**
* ⚠️ **Partially implemented**
* ❌ **Not implemented**

Never claim that something is handled when it is not.

---

## 10. Production Thinking

Discuss relevant:

* Security
* Performance
* Scalability
* Reliability
* Maintainability
* Error handling
* Resource usage
* Concurrency

Clearly distinguish between:

### Implemented

What the current implementation already handles.

### Partially Implemented

What exists but still has limitations.

### Not Implemented

What would need to be added later.

Do not add unnecessary production concerns that are unrelated to the task.

---

## 11. Mental Model

Give me a simple mental model of the feature.

Example:

```text
User
 ↓
API
 ↓
Task Manager
 ↓
Queue
 ↓
Worker
 ↓
AI Model
 ↓
Validation
 ↓
Database
 ↓
Response
```

Explain the diagram in simple language.

After reading the document, I should be able to explain the feature **without looking at the code**.

---

## 12. Key Takeaways

End with **5–10 important things I should remember**.

Keep each takeaway concise and practical.

---

## 13. What Changed in the Project

Provide a final summary:

```text
Created:
- ...

Modified:
- ...

Deleted:
- ...

Dependencies added:
- ...

Tests added/updated:
- ...
```

Only include things that actually happened.

---

## 14. Current Implementation vs Future Improvements

Clearly separate:

### Current Implementation

What exists right now.

### Future Improvements

What could be improved later.

Do not mix planned functionality with implemented functionality.

---

## 15. Test My Understanding

Finish every learning document with **5 questions**.

Include:

1. Easy question
2. Medium question
3. Code-related question
4. Architecture/"why" question
5. Real-world troubleshooting scenario

**Do NOT provide the answers.**

The questions are meant to test whether I actually understand the implementation.

After I answer them, evaluate my answers and explain any misunderstandings.

---

# File Naming Convention

Create one Markdown file per completed task.

Use:

```text
docs/learning/task-<task-number>-<short-task-name>.md
```

Examples:

```text
docs/learning/task-01-project-setup.md
docs/learning/task-02-database-layer.md
docs/learning/task-03-agent-core.md
docs/learning/task-04-self-correction.md
```

Keep the filename short, descriptive, and consistent.

---

# Git Rule — IMPORTANT

These learning documents are **personal development notes**.

They must **NOT be tracked by Git**.

Add the learning documentation directory to `.gitignore`:

```gitignore
# Local development learning documentation
docs/learning/
```

If `docs/learning/` is already tracked by Git:

1. Do not delete the local files.
2. Remove them from Git tracking.
3. Keep them on the local filesystem.
4. Ensure `.gitignore` prevents them from being tracked again.

Use the appropriate Git command to untrack the directory while preserving the local files.

Do not modify `.gitignore` unnecessarily if the directory is already ignored.

---

# Important Rules

* Never skip the learning document.
* Never move to the next task before completing the document.
* Always document the **actual implementation**.
* Always explain **WHAT + WHY + HOW**.
* Use simple explanations alongside technical explanations.
* Use practical examples.
* Explain important files and modules.
* Explain important code rather than every line.
* Never pretend something is implemented.
* Clearly distinguish current functionality from future improvements.
* Keep the documentation useful as a personal learning reference.
* Keep learning documents local-only.
* **Never commit `docs/learning/` to Git.**

---

# Completion Workflow

Every development task must follow:

```text
UNDERSTAND
    ↓
PLAN
    ↓
IMPLEMENT
    ↓
VERIFY
    ↓
CREATE LEARNING DOCUMENT
    ↓
EXPLAIN WHAT + WHY + HOW
    ↓
EXPLAIN FILES + CODE
    ↓
REAL-WORLD EXAMPLE
    ↓
EDGE CASES + PRODUCTION THINKING
    ↓
KEY TAKEAWAYS
    ↓
5 UNDERSTANDING QUESTIONS
    ↓
TASK COMPLETE
    ↓
NEXT TASK
```

## Core Principle

A task is **not complete** merely because the code works.

```text
Working Code
     +
Technical Understanding
     +
Learning Documentation
     =
Task Complete
```
