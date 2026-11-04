#!/usr/bin/env bash
# Renews each Instagram long-lived token (they last 60 days) and saves the new
# one back into the repo's Actions secrets. Needs GH_TOKEN with permission to
# write this repo's secrets. Tokens are never printed.
set -euo pipefail
ver="${IG_API_VERSION:-v23.0}"
for name in IG_TOKEN_CTSOCCERHUB IG_TOKEN_CLIPTHEORY67; do
  tok="${!name:-}"
  if [ -z "$tok" ]; then echo "$name: not set, skipped"; continue; fi
  resp=$(curl -sS --get "https://graph.instagram.com/refresh_access_token" \
    --data-urlencode "grant_type=ig_refresh_token" --data-urlencode "access_token=$tok")
  new=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' <<<"$resp")
  if [ -z "$new" ]; then
    echo "$name: refresh failed: $(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("error",{}).get("message","unknown error"))' <<<"$resp")"
    exit 1
  fi
  echo "::add-mask::$new"
  gh secret set "$name" --body "$new" --repo "$GITHUB_REPOSITORY"
  echo "$name: renewed"
done
