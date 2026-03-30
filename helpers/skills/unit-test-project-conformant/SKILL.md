---
name: unit-test-project-conformant
description: “Write unit tests that strictly conform to a project’s existing testing structure, patterns, and style. Scans existing test files to learn conventions, identifies assertion libraries and test frameworks in use, and generates new tests matching project patterns. Use when the user asks to write unit tests, add test coverage, create test files, generate specs, or update tests after refactoring.”
---
# Unit Test (Project-Conformant)

Write new tests that are **indistinguishable from existing tests** by learning the project’s testing conventions before writing anything.

## Instructions

### Step 1 — Discover Existing Test Patterns

Before writing any test:

1. Identify the file, function, or class to be tested.
2. Search the project for **at least 2–3 tests** covering the same module, directory, or similar behavior.
3. From those tests, extract the project’s **testing contract**:
   - Test file locations and naming conventions (e.g. `test_*.py`, `*.spec.ts`, `*_test.go`)
   - Test structure: standalone functions, classes, parametrized, fixture-driven, or integration-style
   - Assertion style, mocking approach, and helper utilities used
   - What is intentionally *not* tested

### Step 2 — Match Existing Patterns

Follow discovered conventions exactly:

- **Location**: Add to existing test file if similar code is tested there; only create a new file if similar tests do.
- **Style**: Mirror naming, imports, assertions, fixtures, mocking, and formatting.
- **Coverage level**: Match the project’s depth — if only success paths are tested, do the same; if edge cases are covered, include them.
- **Testing approach**: If similar code is tested indirectly or via integration tests, follow that pattern. Do not create standalone unit tests if the project does not.
- **Reuse**: Search for and use existing fixtures, base classes, utilities, and shared setup. Do not recreate logic that already exists.

### Step 3 — Write and Validate the Test

1. Write the test only after completing discovery.
2. Run the test suite to confirm the new test passes and integrates correctly with existing tests.

## Anti-Patterns

- Inventing new test structure, frameworks, or libraries
- Writing standalone tests when the project uses integration tests
- Adding excessive assertions or mocks not seen elsewhere
- Guessing where tests belong without searching first
