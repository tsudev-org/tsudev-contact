# PHIẾU BÀN GIAO - Kết phiên 10/11/2026 (sau phát hành 26.11.1001)

- **Mã phiếu**: 20261110-02
- **Từ**: agent-contact (phiên `tsudev-contact-ef`) - **Đến**: agent của phiên kế tiếp
- **Thời điểm**: 20:40 10/11/2026
- **Trạng thái**: MỞ - phiên sau đọc phiếu này trước khi nhận việc
- **Khóa**: đã nhả hết (`logs/LOCKS.md` trống). Không có monitor/tác vụ nền nào đang chạy.

## 1. Hiện trạng (đã kiểm chứng, không cần làm lại)

| Hạng mục | Trạng thái |
| --- | --- |
| Mã nguồn | `main` = PySide6 + lõi `src/engine` (thuần Python) + i18n vi/en. Kiến trúc: `docs/ARCHITECTURE.md` |
| Phát hành | `v26.11.1001` trên GitHub Releases: `.exe` 27 MB + `SHA256SUMS.txt` + SBOM `.cdx.json` + attestation |
| Website | https://contact.tsudev.com (Cloudflare Worker `tsudev-contact`, mã ở `website/`, xem `website/README.md`) |
| Repo GitHub | `tsudev-org/tsudev-contact`, public, homepage = contact.tsudev.com, ruleset "Bảo vệ main" (id 26943513) |
| CI | `ci.yml`: ruff, pytest Linux (offscreen) + Windows, pip-audit, gitleaks. CodeQL = default setup của org |
| PR mở | 0 |

## 2. Việc tiếp theo (theo thứ tự - đối chiếu `logs/STATE.md`)

1. **Giấy phép mã nguồn** - CHẶN, cần chủ project quyết: repo public nhưng chưa có `LICENSE`. Khi có quyết định:
   thêm `LICENSE`, ghi vào README + trang `website/src/pages/ban-quyen.astro`, deploy lại website.
2. **QU-STD-AUTH** - chờ `tsudev-standards` xử lý TS-15. Khi có bản quy ước mới: `./scripts/sync-standards.sh`,
   chạy `./scripts/check-standards.sh`, đóng mục này.
3. Gợi ý cho chủ project (không tự làm): dữ liệu thật `danh_ba_102_xa.csv` có 217/958 dòng ô SĐT toàn chữ (lệch cột)
   - mở trong app, "Xuất báo cáo lỗi" để sửa.

## 3. Quy trình bắt buộc (bài học của phiên này)

- **`main` được bảo vệ**: mọi thay đổi qua nhánh + PR, chờ đủ 4 check (`Lint + test (Linux)`, `Test (Windows)`,
  `Quét lộ bí mật (gitleaks)`, `Kiểm quy ước`), merge Squash. Chủ project đã ủy quyền agent tự merge (10/11/2026).
- **PR xếp chồng**: KHÔNG merge PR dưới bằng `--delete-branch` khi còn PR phía trên (GitHub đóng PR trên). Merge ->
  `gh pr edit <trên> --base main` -> xóa nhánh. Đồng bộ bằng `git merge origin/main`, không rebase/force-push
  (force-push bị chặn).
- **Phát hành**: PR đổi `APP_VERSION` (`{YY}.{M}.{DD}{NN}`) + chốt CHANGELOG -> merge -> `gh release create v<ver>
  --target main --notes-file ...` (workflow chỉ đính tệp vào Release đã có) -> chờ workflow -> tải về kiểm
  `sha256sum -c` + `gh attestation verify` -> `cd website && GITHUB_TOKEN=$(gh auth token) npm run build &&
  npx wrangler deploy` để trang Tải về cập nhật.
- **Phụ thuộc**: sửa `requirements*.in` -> `scripts/lock-deps.sh`; cài luôn `--require-hashes`. Dependabot gom PR
  hằng tháng (pip, github-actions, npm `/website`): đối chiếu SHA action mới với tag chính thức trước khi merge.
- **Test**: `python -m pytest -q tests` (venv `.venv`, Qt offscreen). Windows thật:
  `scripts/test-gui-win.ps1` (venv `%TEMP%\tsudev-contact-venv`). Chạy từ WSL: chép repo sang thư mục tạm Windows.
- **Ảnh giao diện**: dùng `QWidget.grab()` với dữ liệu `tests/fixtures/make_samples.py`. KHÔNG chụp màn hình desktop
  (từng chụp nhầm cửa sổ trình duyệt của chủ project).
- Gói lõi tên `engine`, không đặt `core` (`.gitignore` chuẩn chặn). Không sửa `.standards/`.
- Phiếu đã gửi sang repo khác: `tsudev/logs/handover/20261110-04_bao-ket-qua-contact-tsudev-com.md` (chưa commit
  ở repo đó - phiên của repo `tsudev` xử lý).

## Kết quả xử lý

- 11/11/2026 (phiên projects-0c): việc 2 (QU-STD-AUTH) XONG nhờ v3.4.0 (TS-15). Phiếu `20261110-05` (giao diện
  đen + tím) xong, PR #19. Việc 1 (giấy phép mã nguồn) vẫn CHỜ chủ dự án chọn giấy phép.
