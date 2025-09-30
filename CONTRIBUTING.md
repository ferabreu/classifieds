# Contributing to ferabreu/classifieds

Welcome! Whether you're the main developer or an occasional contributor, this document explains how to collaborate, keep things organized, and improve the project.

---

## Table of Contents

- [How to Contribute](#how-to-contribute)
- [Labeling Scheme](#labeling-scheme)
- [Coding Guidelines](#coding-guidelines)
- [Issue and Pull Request Workflow](#issue-and-pull-request-workflow)
- [Releases & Milestones](#releases--milestones)
- [Demo Builds](#demo-builds)
- [Support & Questions](#support--questions)

---

## How to Contribute

1. **Find or create an Issue:**  
   Check if your idea/bug already has an Issue. If not, create one and label it appropriately.

2. **Fork and branch (optional):**  
   If collaborating, fork the repo and create a descriptive branch.

3. **Write clear code and commit messages:**  
   Follow the [Coding Guidelines](#coding-guidelines).

4. **Open a Pull Request:**  
   Reference the related issues in your PR description.

5. **Review and test:**  
   All code should be reviewed—by someone else or yourself after a break.

---

## Labeling Scheme

This project uses a clear labeling scheme to organize issues and pull requests. Please use the most relevant labels when creating or updating issues/PRs.

| Label Name     | Color    | Description                                              |
|----------------|----------|---------------------------------------------------------|
| bug            | #d73a4a  | Something is broken or incorrect                        |
| feature        | #a2eeef  | New user-facing functionality                           |
| enhancement    | #0366d6  | Improvements to existing features                       |
| refactor       | #cfd3d7  | Internal code improvements                              |
| documentation  | #0075ca  | Docs or code comments                                   |
| test           | #e4e669  | Testing, test coverage, or test fixes                   |
| data-seed      | #fbca04  | Demo data, fixtures, or seed scripts                    |
| UI             | #cfd3d7  | User interface, templates, or styling                   |
| backend        | #bfe5bf  | Server-side logic, models, or DB work                   |
| migration      | #5319e7  | Database schema or data migrations                      |
| blocked        | #d4c5f9  | Blocked by another issue or external dependency         |
| critical       | #b60205  | High severity, blocks progress or release               |
| high priority  | #e99695  | Should be addressed soon                                |
| low priority   | #f9d0c4  | Non-urgent, nice to have                                |
| needs review   | #fef2c0  | Needs code/design review before closing/MR              |
| help wanted    | #008672  | Good candidate for outside contributions                |
| question       | #d876e3  | Needs clarification or discussion                       |
| wontfix        | #ffffff  | Not planned to be fixed or addressed                    |
| duplicate      | #cccccc  | Duplicate of another issue                              |
| invalid        | #e4e669  | Not a valid issue, bug, or task                         |
| categories     | #f7c6c7  | Category model/navigation work                          |
| listings       | #e7e7e7  | Listing model/posting work                              |
| auth           | #bfe5bf  | Authentication, login, user management                  |
| images         | #fad8c7  | Image upload, processing, or thumbnails                 |
| demo           | #f7c6c7  | Demo features or presentation polish                    |

**Label Usage Tips:**
- Apply labels for type (bug, enhancement), priority, and affected area/module.
- Use `needs review` only when an issue or PR is ready for final review.
- Use `data-seed` for backend/demo data issues, and `demo` for user-facing features for demonstration.
- Combine labels for clarity (e.g., `bug`, `UI`, `critical`).

---

## Coding Guidelines

- **Style:** Follow [PEP8](https://pep8.org/) for Python code.
- **Naming:** Use descriptive names for variables, functions, and branches.
- **Commits:** Write clear, atomic commit messages that explain “what” and “why.”
- **Testing:** Add or update tests for any new/modified code.

---

## Issue and Pull Request Workflow

1. **Assign labels and, if applicable, milestones.**
2. **Link related issues** in PRs and issues using GitHub keywords (`Closes #123`).
3. **Use checklists** in issues for sub-tasks.
4. **If a bug/feature is large, break it down** into smaller, linked issues.
5. **Review:** Every PR (even solo) should get a final review before merge—use `needs review` to flag.

---

## Releases & Milestones

- Use **milestones** to group issues for each planned release or demo.
- When a milestone’s issues are closed, tag a release (even for internal/demo use).
- Update `CHANGELOG.md` with key changes.

---

## Demo Builds

- Try to keep the `main` branch in a runnable/demoable state.
- Schedule periodic demo builds for yourself—these can be informal but should be tagged with a release.

---

## Support & Questions

- Use the `question` label for anything needing clarification.
- For documentation improvements, use the `documentation` label.

---

Feel free to adapt this guide as the project grows!