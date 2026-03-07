---
name: feature
description: Build a complete feature with tests and documentation
disable-model-invocation: true
argument-hint: [description or plan]
---

Implement the following feature: $ARGUMENTS

Follow this workflow strictly, in order:

## 1. Plan

- Enter plan mode
- Explore the codebase to understand existing patterns, conventions, and architecture
- Design the implementation approach
- Present the plan and get user approval before writing any code

## 2. Implement

- Write the code following existing patterns found in the codebase
- Prefer editing existing files over creating new ones
- Keep changes minimal and focused — don't refactor unrelated code

## 3. Test

- Write tests in `backend/tests/` using pytest
- Cover the main paths: happy path, edge cases, error cases
- Run the tests with `python -m pytest` and fix any failures
- All tests must pass before moving on

## 4. Update README

- If the feature adds or changes user-facing functionality, API endpoints, or project structure, update `README.md`
- Add to the appropriate section (features list, API table, project structure, etc.)
- Don't rewrite existing sections — make targeted additions
