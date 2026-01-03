# License audit (quick)

Checked repository files for explicit "GPL v2 only" / "GPLv2-only" markers.

Findings
- No occurrences of "GPLv2-only", "GPL v2 only", "GPL-2.0-only" or similar were found in the provided files.
- Top-level LICENSE is GPLv3 (GNU GPL v3).
- Some files and docs still contain MIT references / headers (these are permissive and compatible with GPLv3). Examples in this snapshot:
  - app/routes/utils.py — header mentions MIT License
  - README.md — "License: MIT or your choice."

Next action — scan third‑party dependencies
- A script has been added at `scripts/check_licenses.py` to scan `requirements.txt` and query PyPI for license metadata.
- Run locally from the project root:
  ```bash
  python scripts/check_licenses.py
  ```
- The script writes `docs/dependency_licenses.md` with per-package details and a heuristic flag for "GPLv2-only" packages.

Interpreting results and remediation
- If any package is truly "GPL-2.0-only" (not "or later"), you cannot relicense the combined/distributed work under GPL‑3.0-only without permission.
- For flagged packages consider:
  - Replace the dependency with a GPLv3-compatible or permissively licensed alternative.
  - Vendor the code under a compatible license if allowed by the dependency's terms.
  - Contact upstream for relicensing or dual-license permission.
  - Choose to distribute your project under GPL-2.0 (or "GPL-2.0-or-later") instead of GPL-3.0.

Notes and caveats
- The scanner is best-effort; PyPI metadata is not always authoritative. Classifiers are the most reliable hint; the `license` field is often free-form text.
- Always do manual legal review for any package flagged as GPLv2-only before finalizing your repository license.

If you want, I can:
- Run the scanner now on your requirements.txt (if you paste its contents here), or
- Update repository headers to preserve MIT notices while keeping LICENSE at GPLv3 (recommended).

