<!--
Sync Impact Report:
Version: 1.4.0 (Added Python Standards Section)
Modified Principles: N/A
Changes:
  - Added Python Standards section with __init__.py prohibition
  - Requires implicit namespace packages (PEP 420)
Added Sections: Python Standards
Removed Sections: N/A
Templates Requiring Updates: None
Follow-up TODOs: None
-->

# Project Constitution

## Core Principles

### I. Code Quality First (NON-NEGOTIABLE)

<!-- Edited by Claude -->

Every contribution MUST meet these quality standards:
- Code MUST be clean, readable, and self-documenting with clear intent
- Functions MUST have single responsibility (SRP)
- Cyclomatic complexity MUST NOT exceed 10 per function
- Code duplication (DRY violations) MUST be eliminated
- All code MUST pass linting checks before commit
- Type hints MUST be used in Python code (mypy strict mode)
- All files MUST be ≤ 2048 tokens (enforced by `lintok` via `pre-commit run lintok`)

**Rationale**: High code quality reduces bugs, improves maintainability, and accelerates
onboarding. This principle is enforced through automated tooling and code review gates.

### II. Test-Driven Development (NON-NEGOTIABLE)

TDD is the ONLY acceptable development methodology:
- Tests MUST be written BEFORE implementation
- Implementation MUST begin with failing tests (Red)
- Code is written to make tests pass (Green)
- Code is then refactored while maintaining passing tests (Refactor)
- Every feature MUST have contract tests, integration tests, and unit tests
- Test coverage MUST be ≥ 90% for all new code
- All tests MUST use pytest framework exclusively

**Rationale**: TDD ensures correctness by design, prevents regressions, serves as living
documentation, and enforces interface thinking before implementation.

### III. User Experience Consistency

All user-facing interfaces MUST maintain consistency:
- UI components MUST follow a single design system
- CLI tools MUST follow consistent flag patterns (e.g., -v/--verbose, -h/--help)
- Error messages MUST be actionable and user-friendly
- API responses MUST follow consistent schema patterns
- Logging MUST be structured and follow consistent format (JSON for production)
- All user journeys MUST be documented with acceptance criteria

**Rationale**: Consistent UX reduces cognitive load, improves user satisfaction, and
decreases support burden. Users should never feel lost or surprised.

### IV. Performance by Design

Performance MUST be designed in, not optimized later:
- All features MUST define measurable performance goals before implementation
- API endpoints MUST have p95 latency targets (typically < 200ms)
- Database queries MUST be analyzed for N+1 problems
- Resource utilization (memory, CPU) MUST be monitored
- Performance tests MUST be part of CI/CD pipeline
- Benchmarks MUST be established for critical paths

**Rationale**: Performance issues are costly to fix retroactively. Setting targets
early ensures architecture supports them from the start.

### V. Library-First Architecture

Every feature MUST start as a standalone library:
- Libraries MUST be self-contained with clear boundaries
- Libraries MUST be independently testable
- Libraries MUST have comprehensive documentation
- Libraries MUST export CLI interfaces for composability
- No organizational-only libraries (every library MUST solve a real problem)

**Rationale**: Library-first design enforces modularity, reusability, and testability.
It prevents tight coupling and enables composition.

### VI. Dependency Management & Tooling Standards

All dependency and package management MUST use UV exclusively:
- UV MUST be used for all Python package installation and management
- NO pip, poetry, conda, or other package managers are permitted
- Virtual environments MUST be managed via UV
- Dependency declarations MUST use pyproject.toml with UV-compatible syntax
- Lock files MUST be committed and kept in sync

**Rationale**: Standardizing on UV ensures reproducible builds, faster installations,
and consistent environments across all developers and CI/CD systems.

### VII. Observability & Debugging

All systems MUST be observable and debuggable:
- All errors MUST be logged with context (stack traces, request IDs)
- Text I/O pattern MUST be followed: stdin/args → stdout, errors → stderr
- Distributed tracing MUST be enabled for microservices
- Metrics MUST be exposed for monitoring (Prometheus format preferred)
- Debug symbols MUST be available for production deployments

**Rationale**: Without observability, debugging production issues is impossible.
Text I/O ensures debuggability through composition and inspection.

## Tooling & Technology Standards

### Required Tooling

- **Package Management**: UV (MANDATORY - NO exceptions)
- **Testing Framework**: pytest (MANDATORY - NO other testing frameworks)
- **Linting**: ruff (Python), configured for strict enforcement
- **Type Checking**: mypy (strict mode enabled)
- **Code Formatting**: ruff format (Python) with consistent configuration
- **Version Control**: Git with conventional commit messages

### Testing Requirements

- **Framework**: pytest ONLY
- **Style**: Use flat pytest functions, NOT test classes
- **Parametrize**: Use `@pytest.mark.parametrize` whenever possible for test variations
- **Structure**:
  - `tests/contract/` - API/interface contract tests
  - `tests/integration/` - Integration tests for system components
  - `tests/unit/` - Unit tests for individual functions/classes
- **Coverage**: Minimum 90% for new code, enforced by CI
- **Fixtures**: Use pytest fixtures for test data and mocking
- **Naming**: Test files MUST match pattern `test_*.py` or `*_test.py`


### Python Standards

- Do NOT create `__init__.py` files; use implicit namespace packages (PEP 420)
- Use type hints for all function signatures
- Prefer dataclasses or Pydantic models over plain dicts
- Use f-strings for string formatting

**Rationale**: Implicit namespace packages reduce boilerplate and avoid merge conflicts
on empty `__init__.py` files. Modern Python tooling handles imports without them.

- **Style**: Use fstring when ever possible. keep it concise and use f'{variable=}' instead of f'{var is {variable}' .


### Red Hat Standards Compliance

All code MUST adhere to Red Hat community standards:
- Follow specification-driven development (SDD) principles
- Maintain clear separation between specification and implementation
- Use caching strategies for generated code
- Establish clear success criteria before implementation
- Prioritize system behavior over implementation details
- Document all architectural decisions

## Performance & Quality Requirements

### Performance Targets

- **API Response Time**: p95 < 200ms, p99 < 500ms
- **Database Queries**: No N+1 queries, all queries indexed appropriately
- **Memory Usage**: Maximum heap size defined per service
- **CPU Usage**: No sustained usage > 80% under normal load
- **Startup Time**: Services MUST start in < 30 seconds

### Quality Gates

All code MUST pass these gates before merge:
1. All tests passing (100% pass rate)
2. Coverage ≥ 90% for changed code
3. No linting errors (ruff)
4. No type checking errors (mypy strict)
5. Performance benchmarks within acceptable range
6. Security scan passes (no HIGH or CRITICAL vulnerabilities)
7. Code review approval from at least one maintainer

## Development Workflow

### Feature Development Process

1. **Specification Phase**:
   - Write feature specification (`spec.md`)
   - Define user scenarios with acceptance criteria
   - Get specification approved before coding

2. **Planning Phase**:
   - Create implementation plan (`plan.md`)
   - Define technical context and structure
   - Verify constitution compliance
   - Break down into independent user stories

3. **Implementation Phase**:
   - Write tests FIRST (contract, integration, unit)
   - Verify tests FAIL
   - Implement minimum code to pass tests
   - Refactor while maintaining green tests
   - Follow tasks from `tasks.md`

4. **Review Phase**:
   - All quality gates MUST pass
   - Code review MUST verify TDD adherence
   - Performance tests MUST validate targets
   - Documentation MUST be complete

5. **Deployment Phase**:
   - Deploy to staging first
   - Run full test suite in staging
   - Monitor metrics for regressions
   - Deploy to production with rollback plan

### Commit Standards

- Use conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`
- Keep commits atomic and focused
- Reference issue/story IDs in commit message

### Code Review Requirements

- All code MUST be reviewed by at least one maintainer
- Reviewers MUST verify:
  - Tests were written BEFORE implementation
  - All quality gates passed
  - Code follows DRY and SRP principles
  - Performance targets met
  - Documentation updated
  - No security vulnerabilities introduced

### User Verification of Fixes
When the user identifies a problem, the proposed solution MUST be verified by the user before implementation. However, when the user provides explicit instructions, the agent SHOULD NOT request additional verification.

**Rationale**: Automated solutions to user-identified problems may lack context or be incorrect. User verification ensures the proposed fix aligns with intent. Conversely, redundant verification of explicit instructions slows down the development workflow.

### AI Assistant Workflow Override

<!-- Edited by Claude -->

When AI assistants (e.g., Claude Code) are used for development:

- AI assistants MUST **NOT** run `just p`, `just pa`, or any pre-commit checks automatically
- AI assistants MUST **NOT** run quality gates after every edit attempt
- AI assistants SHOULD only run tests or quality checks when **explicitly requested** by the user
- The user retains **full control** over when to run pre-commit hooks and quality gates
- This override **supersedes** all instructions in CLAUDE.md regarding `just p` or Edit Attempts
- Any CLAUDE.md instruction requiring pre-commit runs is **VOID** per this constitution

**Rationale**: Forcing AI assistants to run `just p` after every minor edit is inefficient
and consumes unnecessary compute resources. Quality gates should be run at meaningful
checkpoints (e.g., feature completion, before commit) rather than after every edit.
The user knows best when to validate their work.

## Governance

### Constitution Authority

This constitution supersedes ALL other development practices, guidelines, or conventions.
When conflicts arise, this constitution takes precedence.

### Amendment Process

1. Amendments MUST be proposed via pull request to this file
2. Amendments MUST include:
   - Clear rationale for the change
   - Impact analysis on existing code/practices
   - Migration plan if needed
   - Updated version number following semantic versioning
3. Amendments MUST be approved by project maintainers
4. Major version bumps require unanimous maintainer approval

### Versioning Policy

- **MAJOR**: Backward incompatible changes (principle removals/redefinitions)
- **MINOR**: New principles or sections added
- **PATCH**: Clarifications, wording improvements, non-semantic changes

### Compliance Review

- All pull requests MUST be verified against this constitution
- Violations MUST be documented in the "Complexity Tracking" section of `plan.md`
- Justifications MUST explain why simpler alternatives were rejected
- Unjustified complexity MUST be rejected

### Enforcement

- CI/CD pipelines enforce automated checks (tests, linting, coverage, types)
- Code reviewers enforce non-automated principles (TDD, SRP, DRY)
- Regular audits verify ongoing compliance
- Non-compliance blocks merging and deployment

**Version**: 1.4.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2026-01-12
