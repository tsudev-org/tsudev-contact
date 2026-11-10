# PHIẾU BÀN GIAO - Nâng cấp toàn diện tsudev-contact

- **Mã phiếu**: 20261110-01
- **Từ**: agent-contact - **Đến**: phiên sau / chủ project
- **Thời điểm**: 17:45 10/11/2026
- **Ủy quyền**: chủ project cấp toàn quyền (chat 10/11/2026): Việt hóa mặc định, bỏ Facebook, website tên miền con, gia cố bảo mật, tự build/chạy thử trên máy.

## Đã xong (4 PR xếp chồng, chưa merge - agent bị chặn tự merge)
| PR | Nhánh | Nội dung |
| --- | --- | --- |
| #9 | `chore/don-nen-nhan-dien-tsudev` | Bỏ Facebook, icon từ dấu hiệu tsudev, token `.standards/`, README hạng C |
| #10 | `feat/giao-dien-pyside6-va-loi-bao-mat` | PySide6, `src/engine`, vá chèn vCard, i18n, khóa hash, SBOM |
| #11 | `ci/chuoi-cung-ung-va-chung-thuc` | CI, attestation, Dependabot (đã merge #10 vào, không rebase) |
| #12 | `feat/website-contact-tsudev` | Website `contact.tsudev.com` (chưa deploy) |

## Kiểm chứng
- 84 test (Linux offscreen + Windows Python 3.11 thật), ruff sạch, pip-audit 0 lỗ hổng, CI GitHub xanh.
- Build `.exe` thật 25,7 MB, chạy thật trên Windows. Website: check-dist, a11y (9 trang x 3 chế độ), theme: 0 lỗi.
- Tệp thật `danh_ba_102_xa.csv` (chỉ đọc số liệu tổng hợp): 958 dòng -> 738 xuất được; 217 dòng ô SĐT toàn chữ (lệch cột trong dữ liệu gốc) - bản cũ xuất thành `TEL:` vô nghĩa.

## Bước tiếp theo
Xem hàng đợi `logs/STATE.md`: merge #9..#12 -> phát hành bản mới -> deploy website -> đổi homepage -> bật ruleset `main`.

## Lưu ý
- Không chụp màn hình desktop bằng CopyFromScreen (Windows chặn đưa cửa sổ lên trước, chụp nhầm cửa sổ khác). Dùng `QWidget.grab()`.
- Venv test Windows: `%TEMP%\tsudev-contact-venv` (do `scripts/test-gui-win.ps1` tạo, dùng lại được).
