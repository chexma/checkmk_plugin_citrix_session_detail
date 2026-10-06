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
  installed as a plugin and updated on every container start
- `.devcontainer/build.sh` to build the MKP from the `package` manifest

Requirements: Docker (Desktop) and VS Code with the Dev Containers extension.
`initializeCommand` uses `mkdir -p` on the host, i.e. a macOS/Linux host (or WSL).

## Start a new plugin

```bash
git clone <this-template-url> checkmk_plugin_foo
cd checkmk_plugin_foo
git remote rename origin template
git remote add origin <url-of-the-new-plugin-repo>
```

Then:

1. Set `EDITION` and `VARIANT` (Checkmk version) in
   `.devcontainer/devcontainer.json`.
2. Fill in the project section of `CLAUDE.md`.
3. VS Code: "Dev Containers: Reopen in Container".
4. First time only: run `claude` in the container terminal and log in. The
   login lives in the Docker volume `checkmk-claude-config`, which all plugin
   containers share, so this is needed once per machine, not per plugin.
5. Open the Checkmk GUI via the forwarded port 5000 (Ports view), path `/cmk/`.

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
- Rebuilds pick up a new Checkmk version from `VARIANT`; Claude Code updates
  itself, no rebuild needed for that.
- Several plugin containers can run at once: port 5000 is forwarded to a free
  local port per container.
