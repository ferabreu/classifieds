# .gitignore and Git Tracking Behaviors — Reference Report

## 1. How `.gitignore` Works

- `.gitignore` tells Git which files or directories to ignore (not track).
- Patterns can be specific (e.g., `file.txt`), directory-based (e.g., `logs/`), or use wildcards (e.g., `*.log`, `**/temp/`).
- Ignore rules apply recursively from the directory containing the `.gitignore` file.

## 2. Common Gotchas

- **Git never tracks empty directories:** Only files are tracked.
- **Negation (`!`) only un-ignores previously ignored files.** If a parent directory is ignored, you must un-ignore all parents up the path.
- **Global `.gitignore`:** Check for global ignore rules with  
  `git config --get core.excludesfile`
- **Multiple `.gitignore` files:** Subdirectories may have their own `.gitignore` files.
- **Case sensitivity:** Git is case-sensitive on Linux, but not on Windows filesystems.
- **Line endings and permissions:** Windows/WSL differences can cause files to appear changed or ignored.

## 3. Debugging Steps

1. **Check why a file is ignored:**
   ```sh
   git check-ignore -v path/to/file
   ```
   Shows the rule and file causing the ignore.

2. **Find all `.gitignore` files:**
   ```sh
   find . -name .gitignore
   ```

3. **Check global ignore file:**
   ```sh
   git config --get core.excludesfile
   ```
   Then review the file if it exists.

4. **Refresh Git index if files/directories are not tracked as expected:**
   ```sh
   git rm -r --cached .
   git add .
   ```

5. **Unstage all staged files but keep content:**
   ```sh
   git reset
   ```

6. **Force-add a file if needed:**
   ```sh
   git add -f path/to/file
   ```

## 4. `.gitignore` Patterns and Their Effects

| Pattern         | Effect                                                        |
|-----------------|--------------------------------------------------------------|
| `app/`          | Ignores the whole `app/` dir and all its contents            |
| `!app/`         | Un-ignores the dir (but not its files unless `!app/**` used) |
| `!app/**`       | Un-ignores everything under `app/`                           |
| `**/misc*/`     | Ignores any directory named `misc*` anywhere                 |
| `templates/`    | Ignores any top-level `templates` dir                        |
| `**/templates/` | Ignores any dir named `templates` anywhere                   |

## 5. WSL and Windows-Specific Notes

- Prefer working inside the WSL home directory (e.g., `/home/username/project`) to avoid Windows filesystem quirks.
- Avoid switching between Windows and Linux paths in the same repo.
- Case, permission, and line-ending differences may cause confusion or ignored/untracked files.

## 6. Sample `.gitignore` Troubleshooting Scenario

If `git add path/to/file` says the file is ignored, but no pattern matches:
- Confirm with `git check-ignore -v path/to/file`
- Check for global ignore rules.
- Check for hidden or nested `.gitignore` files.
- Make sure the file is not only present in an ignored (or previously ignored) parent folder.
- If all else fails, refresh the index with `git rm -r --cached .` and `git add .`

## 7. Key Commands Reference

| Purpose                                 | Command                                      |
|------------------------------------------|----------------------------------------------|
| See what is tracked/unstaged             | `git status`                                 |
| Unstage everything, keep changes         | `git reset`                                  |
| Remove everything from index, keep files | `git rm -r --cached .`                       |
| Add everything not ignored               | `git add .`                                  |
| Check why a file is ignored              | `git check-ignore -v path/to/file`           |
| Check global ignore file                 | `git config --get core.excludesfile`         |

---

**Prepared by:** Number One (GitHub Copilot)  
**Date:** 2025-08-11
