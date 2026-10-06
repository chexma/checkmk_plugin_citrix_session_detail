ARG EDITION=cloud
ARG VARIANT=2.4.0p27
FROM checkmk/check-mk-${EDITION}:${VARIANT}

# Create the site "cmk" at build time instead of on first container start.
RUN /docker-entrypoint.sh /bin/true

# Basic development tools
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
 && apt-get install -y --no-install-recommends \
    less \
    git \
    sudo \
    man-db \
    unzip \
    gnupg2 \
    gh \
    jq \
    vim \
    curl \
    ca-certificates \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV DEVCONTAINER=true
ENV EDITOR=vim
ENV VISUAL=vim

COPY --chmod=644 requirements.txt /tmp/requirements.txt

USER cmk

# Python dev tools go into the site's local/lib/python3. Do not pin packages
# that Checkmk itself ships (urllib3, requests, pytest, ...): a local copy
# shadows the shipped one and you end up testing against a different library
# than production sites run.
RUN PATH="/omd/sites/cmk/bin:${PATH}" \
    OMD_ROOT="/omd/sites/cmk" \
    /omd/sites/cmk/bin/pip3 install --no-cache-dir -r /tmp/requirements.txt

# Claude Code via the native installer, as cmk: it installs into $HOME
# (~/.local/bin/claude -> ~/.local/share/claude/versions/<version>), so
# `claude update` and auto-updates work without root.
# HOME is set explicitly because Docker does not set it when switching USER.
# CLAUDE_CODE_VERSION=latest is resolved at build time and the layer is cached;
# a stale version is not a problem, Claude Code updates itself afterwards.
ARG CLAUDE_CODE_VERSION=latest
RUN curl -fsSL https://claude.ai/install.sh -o /tmp/claude-install.sh \
 && HOME=/omd/sites/cmk bash /tmp/claude-install.sh "${CLAUDE_CODE_VERSION}" \
 && rm -f /tmp/claude-install.sh \
 && mkdir -p /omd/sites/cmk/.claude

# devcontainer.json builds its PATH from ${containerEnv:PATH}, so this is what
# makes `claude` resolvable in the VS Code remote environment.
ENV PATH=/omd/sites/cmk/.local/bin:${PATH}

ENTRYPOINT ["/bin/bash"]
