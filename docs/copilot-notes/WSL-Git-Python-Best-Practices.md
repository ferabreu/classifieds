# Best Practices for Python Development with Git and WSL

These guidelines will help you avoid common cross-OS and Git pitfalls when developing Python projects in Windows using WSL (Windows Subsystem for Linux).

---

## 0. **Setting Up Visual Studio Code (VSCode) for Python/Flask Development in WSL**

If you've never used VSCode before, don't worry! Here are step-by-step instructions to get you started with Python/Flask development in WSL.

### **Step 1: Install the "Remote - WSL" Extension**

1. Open VSCode (on Windows).
2. Go to the Extensions view by clicking the square icon on the sidebar or pressing <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>X</kbd>.
3. Search for **"Remote - WSL"**.
4. Click **Install**.

### **Step 2: Open Your Project Folder in WSL**

1. Open your WSL terminal (e.g., Ubuntu).
2. Navigate to your project directory, ideally stored in `/home/<your-username>/...`.
    ```sh
    cd ~/dev/yourproject
    ```
3. Launch VSCode in this folder by running:
    ```sh
    code .
    ```
   - The first time you do this, VSCode may prompt to install server components in WSL—choose "Yes".

### **Step 3: Install the Python Extension (Inside WSL)**

1. Once VSCode opens, it should show "WSL: Ubuntu" (or your distro) in the bottom-left green bar.
2. Go to the Extensions view (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>X</kbd>).
3. Search for **"Python"** (by Microsoft).
4. Click **Install**. Make sure it says "WSL: Ubuntu" in the install button.

### **Step 4: (Optional but Recommended) Install the Flask Extension**

- You may also install the **Flask Snippets** or **Flask Support** extensions for handy code snippets.

### **Step 5: Select the Python Interpreter**

1. Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> to open the Command Palette.
2. Type and select **Python: Select Interpreter**.
3. Choose the interpreter from your WSL environment (e.g., `/usr/bin/python3` or a virtualenv in your project).

### **Step 6: (Optional) Create and Use a Virtual Environment**

1. In the VSCode terminal (which should be WSL/bash), create a virtual environment:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2. Re-run "Python: Select Interpreter" and pick the new virtualenv.

### **Step 7: Run and Debug Your Flask App**

- You can run your Flask app from the VSCode terminal:
    ```sh
    flask run
    ```
- For debugging:
    1. Go to the "Run & Debug" sidebar (play icon with a bug).
    2. Click "create a launch.json file".
    3. Select "Flask"—VSCode will auto-generate debug config.
    4. Set breakpoints and start debugging!

### **Step 8: Install Other Useful Extensions**

- **Pylance**: Fast, smart Python language support.
- **Black Formatter**: Auto-format your code.
- **GitLens**: Supercharges Git in VSCode.

---

You are now set up for modern Python/Flask development in WSL using VSCode!

---

## 1. **Keep Your Code in the WSL Filesystem**

- **Store your git repositories in `/home/<your-username>/...` inside WSL** (not `/mnt/c/` or `/mnt/d/`).  
  - The Linux filesystem avoids NTFS/Windows quirks: case sensitivity, permissions, file locking, and performance problems.
- **How to move your project:**
  ```sh
  mv /mnt/d/Users/yourname/dev/project /home/yourname/dev/
  ```

## 2. **Use WSL-Terminal Git Exclusively**

- **Do all your git operations in the WSL terminal.**
- Do NOT mix Git usage between Windows (Git Bash, Windows command line, GUI tools) and WSL.  
  - Mixed usage can corrupt your working directory, index, or cause phantom changes.

## 3. **Edit Code Using WSL-Friendly Editors**

- **Best:** Use VSCode with the “Remote - WSL” extension.  
  - Launch via `code .` from your WSL terminal in your project folder.
  - VSCode then runs all code, git, and extensions inside WSL.
- **Acceptable:** Use Linux editors (vim, nano, emacs, etc.) inside WSL.
- **Avoid:** Editing files in WSL using Windows editors (Notepad++, Sublime, Windows VSCode, etc.), especially if your repo is on the Linux filesystem.  
  - If you must use Windows editors, only do so for repos in `/mnt/c/...`, and accept the risk of occasional index confusion.

## 4. **Be Careful with Line Endings**

- Always use LF (`\n`) for Python projects.
- Help enforce this with a `.gitattributes` file:
  ```
  * text=auto
  *.py eol=lf
  ```
- In VSCode, set `"files.eol": "\n"` in your settings.

## 5. **Avoid Case-Only Renames and Mixed-Case Folders**

- On NTFS (Windows) filesystems, renaming from `foo` to `Foo` can cause Git confusion.
- Use `git mv` for any filename or directory rename, not file explorer.

## 6. **Watch for .gitignore and Hidden Ignore Files**

- Use `git check-ignore -v <file>` to debug ignored files.
- Check for `.gitignore` files in your project root, subdirectories, `.git/info/exclude`, and your global gitignore (`git config --get core.excludesfile`).

## 7. **Never Track Empty Directories**

- Git does not track empty folders. If you need a directory to exist, add a blank `.gitkeep` file.

## 8. **Commit and Push Frequently**

- After big changes or moves, commit and push early and often. This protects your work and makes recovery easier.

## 9. **Use Branches for Major Refactors**

- Branches let you experiment safely and revert or merge cleanly.

## 10. **Learn Essential Git Commands**

- Discard changes: `git restore <file>`
- Unstage a file: `git reset HEAD <file>`
- Stash changes: `git stash`
- Debug ignored files: `git check-ignore -v <file>`
- See status: `git status`

## 11. **If You Hit a Weird Problem**

- Don’t “force” through with `-f` or random commands.
- Run:
  - `git status`
  - `git check-ignore -v <file>`
  - `find . -name ".gitignore"`
- Paste outputs into a new issue, commit message, or share with a teammate for help.

---

## Quick Reference Table

| Task                          | Best Practice                                   |
|-------------------------------|-------------------------------------------------|
| Store code                    | WSL home directory (`/home/yourname/...`)       |
| Use Git                       | Only in WSL terminal                            |
| Edit code                     | VSCode (Remote WSL) or Linux editors in WSL     |
| Line endings                  | LF only, enforce with `.gitattributes`          |
| Rename files/dirs             | Use `git mv`                                    |
| Check ignore rules            | `git check-ignore -v <file>`                    |
| Keep empty folders            | Add `.gitkeep`                                  |
| Commit often                  | Early, often, and after big changes             |
| Big changes                   | Use feature branches                            |

---

## Troubleshooting Checklist

- [ ] Is your repo in `/home/...`?
- [ ] Are you only using WSL for Git commands?
- [ ] Are you only editing files with WSL-aware editors?
- [ ] Are line endings consistently LF?
- [ ] No force-adding files unless you know the ignore rule?
- [ ] No case-only renames without `git mv`?
- [ ] No empty directories without `.gitkeep`?
- [ ] Do you check `.gitignore` and ignored file status if something seems off?

---

**Following these guidelines will help you avoid almost all cross-platform Git headaches and keep your Python workflow smooth in WSL!**