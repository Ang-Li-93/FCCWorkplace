#!/usr/bin/env bash
#
# clone_local_forks.sh
# --------------------
# Add the user's editable forks of k4geo and k4Reco as git SUBMODULES of the
# FCCWorkplace superproject (alongside FCCAnalyses, EventProducer, ...).
# Everything uses SSH (git@github.com), matching the existing .gitmodules.
#
#   bash fcc_maps_wrapper_pixesl/setup/clone_local_forks.sh
#
# Run this from a shell where your GitHub SSH key is usable (ssh-agent loaded,
# or an unencrypted ~/.ssh/id_ed25519_github). Test first with:
#   ssh -T git@github.com
#
# Submodule paths (under the superproject root):
#   k4geo  -> ./k4geo    from git@github.com:Ang-Li-93/k4geo.git
#   k4Reco -> ./k4Reco   from git@github.com:Ang-Li-93/k4Reco.git
# Override the URLs via env K4GEO_FORK / K4RECO_FORK; branches via
# K4GEO_BRANCH / K4RECO_BRANCH (default: the fork's default branch).

set -euo pipefail

K4GEO_FORK="${K4GEO_FORK:-git@github.com:Ang-Li-93/k4geo.git}"
K4RECO_FORK="${K4RECO_FORK:-git@github.com:Ang-Li-93/k4Reco.git}"

# --- locate the superproject (FCCWorkplace) root --------------------------
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$ROOT" ]; then
    echo "ERROR: not inside a git repository. Run this from within FCCWorkplace." >&2
    exit 1
fi
cd "$ROOT"
echo "[submod] superproject root : $ROOT"

# --- pre-flight: SSH auth to GitHub ---------------------------------------
if ! GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=10' \
        git ls-remote "$K4GEO_FORK" HEAD >/dev/null 2>&1; then
    echo "ERROR: cannot reach $K4GEO_FORK over SSH (publickey?)." >&2
    echo "       Load your key first, e.g.:" >&2
    echo "         eval \$(ssh-agent -s) && ssh-add ~/.ssh/id_ed25519_github" >&2
    echo "       then verify:  ssh -T git@github.com" >&2
    exit 1
fi

add_submodule() {
    local url="$1" path="$2" branch="${3:-}"
    if [ -e "$path/.git" ] || git config -f .gitmodules --get "submodule.$path.url" >/dev/null 2>&1; then
        echo "[submod] '$path' already a submodule; updating..."
        git submodule update --init --recursive "$path" || true
        return 0
    fi
    if [ -e "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        echo "ERROR: '$path' exists and is non-empty but is not a submodule." >&2
        echo "       Move it aside before adding the submodule." >&2
        exit 1
    fi
    echo "[submod] adding $url -> $path"
    if [ -n "$branch" ]; then
        git submodule add -b "$branch" "$url" "$path"
    else
        git submodule add "$url" "$path"
    fi
}

add_submodule "$K4GEO_FORK"  "k4geo"  "${K4GEO_BRANCH:-}"
add_submodule "$K4RECO_FORK" "k4Reco" "${K4RECO_BRANCH:-}"

cat <<EOF

================================================================
Submodules added (staged, not committed):
  k4geo  -> $ROOT/k4geo
  k4Reco -> $ROOT/k4Reco

Review and commit when ready:
  git status
  git add .gitmodules k4geo k4Reco
  git commit -m "Add k4geo and k4Reco forks as submodules"

Then set up the project environment (auto-detects the new submodules):
  source setup_MAPS.sh

Notes:
 * k4geo is pure geometry XML -- edit FCCee/ALLEGRO/... directly, no build.
 * k4Reco must be BUILT before k4_local_repo picks it up (see k4Reco/README.md).
================================================================
EOF
