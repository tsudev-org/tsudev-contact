#!/usr/bin/env bash
# Khóa phụ thuộc kèm hash cho MỌI nền tảng (Windows build + Linux CI) bằng uv.
# Chạy lại sau khi sửa requirements*.in. Cài đặt luôn dùng: pip install --require-hashes -r <file>.
set -euo pipefail
cd "$(dirname "$0")/.."
UV="${UV:-uv}"
"$UV" pip compile --universal --python-version 3.11 --generate-hashes --quiet \
  --output-file requirements.txt requirements.in
"$UV" pip compile --universal --python-version 3.11 --generate-hashes --quiet \
  --output-file requirements-dev.txt requirements-dev.in
echo "Đã khóa requirements.txt và requirements-dev.txt"
