# Contributing to twig-stix

Thank you for contributing! 

This guide outlines how you can contribute to `twig-stix`. 

## 1. Branching and Feature Work

| Type | Branch Prefix | Description | Merge Timing |
|------|----------------|--------------|---------------|
| Bug fix | `fix/` | Patches or small improvements | Anytime |
| Docs | `docs/` | Improvements to documentation without changes to functionality | Anytime |
| Enhancement | `feat/` | New features or updates | Before code freeze |
| Proof of Concept | `poc/` | Exploratory or experimental work | Not merged until reviewed |
| Refactor | `refactor/` | Structural reorganization | Requires discussion before starting |

**Branching Principles**
* Keep branches small and purposeful; one concept per PR
* Large or multi-feature PRs are discouraged; split them by concern
* Tag experimental branches clearly (`poc/ai-generated-utility`)

## 2. Process for Major Changes

1. **Open an Issue** before starting a large refactor or new feature.
2. **Discuss scope and timing** with the lead dev or tech manager (especially before ISPA season).
3. **Link commits** to issues (e.g., `Closes #12`).
4. **Request a review** before merging into `main`.
5. **Describe rationale** for improvements, including motivation and context, expected impact, testing and validation plan. Include your thoughts about scalability, reproducibility, and replicability while considering the needs of our PHU and other PHUs across Ontario.

## 3. Code Standards

- **Python:**
    * Include docstrings and type hints on all new functions and classes
    * Maintain consistent logging and clear variable naming
    * Keep functions modular; small, testable, single purpose 

- **Commit messages:** Be descriptive and reference issues. Co-pilot is a great tool for this.