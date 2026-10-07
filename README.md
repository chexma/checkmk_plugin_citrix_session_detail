# Checkmk plugin development template

Devcontainer template for developing Checkmk extensions (agent-based checks,
special agents, rulesets, graphing, bakery plugins, MKPs) with a real Checkmk
site and Claude Code. Clone it once per plugin.

What you get:

- A Checkmk site `cmk` (official `checkmk/check-mk-<edition>` image), started
  on every container start, GUI login `cmkadmin`/`cmkadmin`
- Workspace directories bind-mounted into the site's `local/` hierarchy, so
  plugin changes are live without copying
- Python tooling: pytest (shipped with Checkmk) plus pytest-cov and
  requests-mock in the site Python; black, isort and flake8 in a separate venv
  (configured in `pyproject.toml` / `.flake8`)
- Claude Code (native installer, updates itself) with the
  [checkmk-plugin-dev skill](https://github.com/chexma/claude_code_checkmk_plugin_skill),
  installed as a plugin and updated on every container start. Project
  settings in `.claude/settings.json`: routine commands (pytest, black, isort,
  flake8, `cmk -v`, `ci.sh`, `test-host.sh`) run without prompts,
  `mkp release`/`mkp disable` are denied, and a hook formats every Python
  file Claude edits with black/isort
- `.devcontainer/build.sh` to build the MKP from the `package` manifest
- `.devcontainer/test-host.sh` to create a host whose agent output comes from
  a file, for discovery/check runs against canned data
- GitHub Actions (`.github/workflows/ci.yml`): lint, pytest and
  `cmk-validate-plugins` in the devcontainer image on every push; on a tag
  `v<version>` also the MKP as a GitHub release

Requirements: Docker (Desktop) and VS Code with the Dev Containers extension.
`initializeCommand` uses `mkdir -p` on the host, i.e. a macOS/Linux host (or WSL).

## Start a new plugin

```bash
git clone https://github.com/chexma/checkmk-plugin-template.git checkmk_plugin_foo
cd checkmk_plugin_foo
.devcontainer/init-plugin.sh foo <url-of-the-new-plugin-repo>
```

`init-plugin.sh` creates `CLAUDE.local.md` (see below) and `plugins/foo/`,
renames the template remote to `template` and sets `origin`
(leave out the URL to keep the remotes as they are). Then:

1. Set `EDITION` and `VARIANT` (Checkmk version) in
   `.devcontainer/devcontainer.json`.
2. Describe the plugin in `CLAUDE.local.md`, commit.
3. VS Code: "Dev Containers: Reopen in Container".
4. First time only: run `claude` in the container terminal and log in. The
   login lives in the Docker volume `checkmk-claude-config`, which all plugin
   containers share, so this is needed once per machine, not per plugin.
   Caveat: there are reports that Claude instances in several containers
   writing `.claude.json` in that volume at the same moment can corrupt it
   (Claude Code then asks for a new login). If you work that way, give each
   project its own volume (`checkmk-claude-config-${localWorkspaceFolderBasename}`
   in `devcontainer.json`).
5. Open the Checkmk GUI via the forwarded port 5000 (Ports view), path `/cmk/`.

## Claude instructions: CLAUDE.md and CLAUDE.local.md

`CLAUDE.md` is generic (environment, commands, MKP rules), comes from the
template and is tracked. Everything about the plugin itself (purpose,
external system, architecture, conventions) goes into `CLAUDE.local.md`:
Claude Code loads it next to `CLAUDE.md`, but git ignores it, so nothing
about the plugin is exposed in the repo. It exists only on your machine, as
does Claude's memory in the `checkmk-claude-config` volume: keep a copy if
you need it elsewhere.

## Test against canned agent output

```bash
.devcontainer/test-host.sh myhost temp/myhost.agent_output   # or a script with #!
cmk -vI --detect-plugins=<plugin> myhost
cmk -v --detect-plugins=<plugin> myhost
.devcontainer/test-host.sh --remove myhost
```

## CI and releases

`.devcontainer/ci.sh` runs the same checks as CI; run it before pushing.
To release: bump `version` in `package`, commit, then
`git tag v<version> && git push origin v<version>`. CI builds the MKP and
attaches it to a GitHub release; it fails if the tag and `version` differ.

## Migrate an existing plugin

For plugin folders from an older devcontainer setup (with or without git):
`.devcontainer/MIGRATION.md` is a step-by-step guide for Claude Code in the
old container. In that container, ask Claude:

```text
Add https://github.com/chexma/checkmk-plugin-template.git as git remote
"template" (run `git init -b main` first if this is no git repo), fetch it and
follow `git show template/main:.devcontainer/MIGRATION.md`, phase 1.
```

Then rebuild the container in VS Code and, in the new container:
`Follow .devcontainer/MIGRATION.md, phase 2.`

## Get template updates into a plugin repo

```bash
git pull template main
```

Template files (`.devcontainer/`, tool configs) and plugin code don't
overlap, so this usually merges cleanly.

## Layout

| Directory | Mounted / linked to (site `cmk`) | Use |
|---|---|---|
| `plugins/` | `local/lib/python3/cmk_addons/plugins/` | New-style plugins (`<family>/agent_based`, `rulesets`, ...) |
| `lib/` | `local/lib/python3/cmk/` | Library extensions (e.g. bakery v1) |
| `plugins_legacy/` | `local/share/check_mk/` | Legacy plugin locations |
| `agents/` | `local/share/check_mk/agents/` | Agent plugins for the bakery |
| `bin/` | `local/bin/` | Scripts |
| `nagios_plugins/` | `local/lib/nagios/plugins/` | Active check executables |
| `temp/` | `local/tmp/` | Scratch space, not tracked |
| `tests/` | – | pytest |

## Notes

- The container starts the site, cleans stale PID files and refreshes the
  skill plugin on **every** start; the log is
  `~/var/log/devcontainer-poststart.log`.
- `.devcontainer/requirements-site.txt` is installed into the site with
  `--no-deps`: the site's `pip3` always installs with `--target`, which would
  otherwise add local copies of packages Checkmk ships (urllib3, requests,
  pytest, ...) that shadow the shipped ones. List missing dependencies there
  explicitly. Standalone tools go into `requirements-tools.txt` (own venv).
- All tool versions are pinned; bump them deliberately and rebuild. VS Code
  is configured to use the pinned black/isort/flake8 from the image, not the
  ones bundled with its extensions.
- Rebuilds pick up a new Checkmk version from `VARIANT`; Claude Code updates
  itself, no rebuild needed for that.
- The Checkmk images exist for `linux/amd64` only. On Apple Silicon they run
  emulated; enable "Use Rosetta for x86_64/amd64 emulation" in Docker Desktop.
- Releases are documented in `Changelog.md`; built `*.mkp` files are not
  tracked (CI attaches them to the GitHub release).
- Several plugin containers can run at once: port 5000 is forwarded to a free
  local port per container.
