# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository.

## Repository Status

This repository is currently in its initial state. It was created on March 26, 2026, and contains only a `.gitkeep` placeholder. No application code, framework, or tooling has been added yet.

## Repository Info

- **Remote**: `nustanakritwithai/Hih` (GitHub)
- **Default branch**: `main`
- **Development branches**: Follow the `claude/<description>` naming convention (e.g., `claude/add-claude-documentation-EZekt`)

## Git Workflow

- All feature work should be developed on a dedicated branch, never directly on `main`
- Branch names use the format: `claude/<short-description>` for AI-assisted work
- Commit messages should be clear and descriptive, focused on the "why" not just the "what"
- Push branches with `git push -u origin <branch-name>`
- Do NOT push to `main` without explicit user permission

## Conventions for AI Assistants

### Before Making Changes
- Read existing files before editing them
- Understand the current structure before adding to it
- Don't create files unless they are necessary for the task

### Code Style
- Follow the conventions already established in the codebase (when code exists)
- Do not add unnecessary comments, docstrings, or type annotations to code you didn't change
- Avoid speculative abstractions — implement only what the task requires
- Do not introduce security vulnerabilities (injection, XSS, etc.)

### File Management
- Prefer editing existing files over creating new ones
- Do not create README files or documentation unless explicitly requested
- Do not add backwards-compatibility shims or feature flags unless needed

### Testing
- Run existing tests before and after making changes (when tests exist)
- Do not skip or bypass test hooks

### Risky Actions — Always Confirm First
The following require explicit user confirmation before proceeding:
- Deleting files or directories
- Force-pushing any branch
- `git reset --hard` or other destructive git operations
- Pushing to `main`
- Modifying CI/CD pipelines
- Any action visible to others (posting comments, creating PRs)

## Updating This File

When the project gains a defined technology stack, framework, or tooling, update this file to include:
- Technology stack and key dependencies
- How to install dependencies
- How to run the development server
- How to run tests
- Environment variables required (with an `.env.example` reference)
- Build and deployment instructions
- Linting and formatting commands
