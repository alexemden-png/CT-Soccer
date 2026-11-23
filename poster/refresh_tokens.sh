#!/usr/bin/env bash
# Renews Instagram user tokens (start with "IG", last 60 days) and saves the new
# one back into the repo's Actions secrets. Meta system-user tokens (start with
# "EAA") never expire and are left alone. Needs GH_TOKEN with permission to
# write this repo's secrets only when there is an Instagram user token to renew.
# Tokens are never printed.
set -euo pipefail
ver="${IG_API_VERSION:-v23.0}"
for name in IG_TOKEN_CTSOCCERHUB IG_TOKEN_CLIPTHEORY67; do
  tok="${!name:-}"
  if [ -z "$tok" ]; then echo "$name: not set, skipped"; continue; fi
  if [[ "$tok" != IG* ]]; then echo "$name: system-user token, never expires, nothing to renew"; continue; fi
  if [ -z "${GH_TOKEN:-}" ]; then echo "$name: needs renewing, but the GH_SECRETS_TOKEN secret is not set"; exit 1; fi
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
