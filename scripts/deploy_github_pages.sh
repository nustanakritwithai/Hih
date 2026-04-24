#!/usr/bin/env bash
set -euo pipefail

# Deploy helper for GitHub Pages (GitHub Actions based)
# Requirements:
# 1) git remote named origin points to GitHub repo
# 2) repo Settings > Pages > Source: GitHub Actions
# 3) authenticated push access

if ! command -v git >/dev/null 2>&1; then
  echo "git command not found" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "ไม่พบ remote 'origin'" >&2
  echo "เพิ่มก่อนด้วย: git remote add origin https://github.com/<username>/<repo>.git" >&2
  exit 1
fi

remote_url="$(git remote get-url origin)"

# Convert both SSH and HTTPS format to owner/repo
slug=""
if [[ "$remote_url" =~ github.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
  slug="${BASH_REMATCH[1]}"
fi

if [[ -z "$slug" ]]; then
  echo "remote origin ไม่ใช่ GitHub URL ที่รองรับ: $remote_url" >&2
  exit 1
fi

current_branch="$(git branch --show-current)"
echo "กำลัง push branch '$current_branch' ไป origin/main ..."
git push -u origin "$current_branch":main

owner="${slug%%/*}"
repo="${slug##*/}"

echo
echo "ถัดไปให้เปิด Settings > Pages แล้วเลือก Source: GitHub Actions"
echo "เมื่อ workflow ทำงานเสร็จ เว็บจะอยู่ที่:"
echo "https://${owner}.github.io/${repo}/"
