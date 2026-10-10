# Contributing to `kimss`

## Develop

From the package root (`kimss_sdk/` in the monorepo, or the root of the public mirror):

```bash
pip install -e ".[dev,mcp,types]"
pytest tests -v
ruff check kimss/mcp tests examples
```

## Monorepo → public mirror

The main application monorepo syncs this folder to a **public** `kimss-python-sdk` repository via `.github/workflows/mirror_kimss_sdk.yml` (at the root of that monorepo).

**Secrets (GitHub → kimssApi → Settings → Secrets):**

| Secret | Purpose |
|--------|---------|
| `KIMSS_SDK_MIRROR_PAT` | Fine-grained PAT with **Contents: Read and write** on the public mirror repo only |
| `KIMSS_SDK_MIRROR_REPO` | `owner/repo` (e.g. `kimss-ai/kimss-python-sdk`) **without** `https://` or `.git` |

On every push to `main` that touches `kimss_sdk/**`, the workflow runs `git subtree split --prefix=kimss_sdk` and force-pushes to the public repo’s `main`.

## PyPI (trusted publisher)

1. On [pypi.org](https://pypi.org), open **Your projects** → **kimss** → **Manage** → sidebar **Publishing** (`/manage/project/kimss/settings/publishing/`). Add a GitHub trusted publisher: owner **`kimss-ai`**, repository **`kimss-python-sdk`**, workflow filename **`publish.yml`**, environment **blank** (must match the mirror repo that runs the tag workflow — not the personal `kimssai` owner).
2. In the public repo, create a **GitHub Release** from tag `v1.0.0` (or push tag `v1.0.0`) so `publish.yml` runs.
3. Verify: `pip install -U kimss` and `uvx --from 'kimss[mcp]' kimss-mcp-server` with `KIMSS_API_KEY` set in the IDE / Claude Desktop MCP config.

Do not store PyPI passwords in the repo; use OIDC trusted publishing only.

## Version bump & PyPI tag

Full 3-step checklist (monorepo bump → mirror verification → public tag for OIDC publish): **[../plans/2026-05-26-kimss-sdk-release-routine.md](../plans/2026-05-26-kimss-sdk-release-routine.md)**.

Short form: edit `version` in `pyproject.toml`, merge to monorepo `main`, wait for mirror, then tag the **public** repo (`v*.*.*` matching that version).
