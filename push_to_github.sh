#!/usr/bin/env bash
# One-time push of this repo to GitHub, then (optionally) add collaborators.
# Usage:
#   1) gh auth login          # once, interactive — pick GitHub.com > HTTPS > browser
#   2) ./push_to_github.sh [carp_github_username] [tarun_github_username]
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"

REPO="hroc-training"
VISIBILITY="--private"        # change to --public if you want it open

if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in. Run:  gh auth login   then re-run this script."; exit 1
fi

# create the repo from this folder and push current branch (main)
gh repo create "$REPO" $VISIBILITY --source=. --remote=origin --push

URL=$(gh repo view --json url -q .url)
echo "Pushed -> $URL"

# add collaborators if usernames were passed
for user in "$@"; do
  [ -z "$user" ] && continue
  gh api -X PUT "repos/:owner/$REPO/collaborators/$user" -f permission=push \
    && echo "Invited collaborator: $user"
done
echo "Done. Send the repo URL to Carp/Tarun (they'll get an email invite if added)."
