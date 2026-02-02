---
name: unit-test-repo-conformant
description: Guides the agent to write unit tests that strictly conform to the repository's existing testing structure, patterns, and style by learning from similar tests before writing anything new.
---
# Unit Test (Repository-Conformant) Skill

This skill ensures the agent does **not invent test structure** and instead learns how the repository already tests similar code, then writes the new test in the same style, location, and pattern.

The goal is for the new test to be **indistinguishable from existing tests**.

## When to Use

- Use this skill every time a unit test must be written or modified.
- Use this skill when adding coverage for new functions, classes, or behavior.
- Use this skill when refactoring code that requires corresponding test updates.
- This skill is required whenever the agent is tempted to create a “clean” or “ideal” test structure.

## Instructions

### Step 1 — Discover How the Repository Tests Similar Code

Before writing any test:

- Identify the file, function, or class to be tested.
- Search the repository for tests covering:
  - The same module
  - The same directory
  - Similar functions
  - Similar classes
  - Similar behavior
- Use search terms such as:
  - Function name
  - Class name
  - Module name
  - Error messages
  - Public API names

You must examine **at least 2–3 similar tests** before proceeding.

---

### Step 2 — Extract the Test Pattern

From the discovered tests, learn:

- Where tests are located
- File naming conventions
- Test naming conventions
- Whether tests are:
  - Standalone functions
  - Inside classes
  - Parametrized
  - Fixture-driven
  - Integration-style
- Assertion style
- Mocking style
- Helper utilities used
- What is intentionally *not* tested

You are learning the repository’s **testing contract**.

---

### Step 3 — Decide Where the Test Belongs

Follow existing structure exactly:

- If similar code is tested in a shared file → add to that file
- If similar code is tested inside a class → add a method there
- If similar tests extend parametrization → extend it
- If similar behavior is only tested indirectly → do the same

Do **not** create a new test file unless similar tests do.

---

### Step 4 — Match Style Exactly

Mirror the repository’s style for:

- Function and variable names
- Imports
- Assertion style
- Fixtures
- Mocking
- Test utilities
- Formatting and layout

Do not introduce new libraries, helpers, or patterns.

---

### Step 5 — Respect How the Repository Chooses to Test

If similar methods:

- Are tested indirectly
- Are tested via integration tests
- Are not given standalone unit tests

Then you must follow the same pattern.

Do **not** create standalone unit tests if the repository does not.

---

### Step 6 — Match the Level of Coverage

Match the repository’s expectations:

- If tests check only success paths → do the same
- If tests include edge cases → include them
- If tests include error cases → include them
- If tests use heavy mocking → do the same
- If tests avoid mocking → avoid it

Do not over-test compared to existing patterns.

---

### Step 7 — Reuse Existing Helpers and Fixtures

Search for and reuse:

- Fixtures
- Base test classes
- Utilities
- Custom assertions
- Shared setup logic

Do not recreate logic that already exists.

---

### Step 8 — Write the Test Last

Only after completing all discovery steps should you write the test.

The result should look like it was written by the same author as the surrounding tests.

---

## Anti-Patterns (Never Do These)

- Creating new test structure because it seems “better”
- Writing standalone tests when the repo does not
- Introducing new testing frameworks
- Adding excessive assertions not seen elsewhere
- Adding mocks where the repo avoids them
- Guessing where tests belong without searching

---

## Final Checklist

Before finishing, confirm:

- Test is in the correct location
- Naming matches existing tests
- Structure matches existing tests
- Assertions match existing tests
- Fixtures/helpers are reused
- No new patterns introduced
- Coverage level matches similar tests

---

Use the ask questions tool if you need to clarify requirements with the user.
