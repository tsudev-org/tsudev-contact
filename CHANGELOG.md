# CHANGELOG - tsudev-contact

Mỗi bản phát hành 1 dòng, định dạng: `{version} - {DD/MM/YYYY} - nội dung thay đổi`.
Quy ước đặt tên bản phát hành: `.standards/docs/VERSIONING.md` mục 2.

## Chưa phát hành

- **CI**: workflow `CI` mỗi PR (ruff, pytest Linux + Windows, pip-audit, gitleaks ghim checksum); phát hành ghim action theo SHA, cài theo hash, kèm SBOM và **chứng thực nguồn gốc bản build** (`gh attestation verify`); Dependabot hằng tháng.
- **Giao diện mới bằng PySide6 (Qt 6)**: 3 bước trên một màn hình, kéo-thả tệp, tự ghép cột kèm giá trị mẫu, tự kiểm tra dữ liệu, bảng xem trước lọc/tìm không dấu/phân trang chuẩn `DATA_TABLE.md` (QU-STD-TABLE), chủ đề Theo hệ thống/Sáng/Ấm/Tối, font Inter, hộp thoại Giới thiệu nối về tsudev.com. Bỏ màn hình hiệu ứng khởi động.
- **Tiếng Việt mặc định + tiếng Anh** (`src/i18n/`).
- **Bảo mật**: sửa lỗ hổng chèn vCard (ô chứa xuống dòng sinh được liên hệ giả); thoát ký tự RFC 6350 và gập dòng mọi trường; bỏ ký tự vô hình/đảo chiều chữ; trần kích thước tệp/dòng/cột/ô; không còn bỏ lặng lẽ ký tự hỏng; báo cáo lỗi chống chèn công thức; danh bạ chỉ giữ trong RAM và xóa CSDL tạm bản cũ để lại trong %TEMP%; ghi tệp nguyên tử.
- **Dữ liệu**: chuẩn hóa SĐT Việt Nam (+84, thêm số 0 bị Excel làm mất, nhiều số một ô), email, ngày sinh (cả số ngày kiểu Excel), phát hiện trùng số; thêm trường Chức vụ; vCard có `N`, CRLF, `REV` theo UTC thật.
- **Chuỗi cung ứng**: phụ thuộc khóa phiên bản + hash, SBOM CycloneDX đi kèm bản phát hành, pip-audit, ruff.
- Bản `.exe` có siêu dữ liệu nhà phát hành tsudev, bỏ UPX, loại module Qt không dùng (kể cả mạng).
- Bỏ liên kết Facebook; liên kết hỗ trợ trỏ về trang sản phẩm `https://contact.tsudev.com`. Nhà phát hành ghi `tsudev`.
- Icon ứng dụng sinh từ dấu hiệu thu gọn tsudev (`tools/gen_icons.py`, `.ico` nhiều lớp 16 tới 256); bỏ `icon.ico`, `icon.png`, `lock.png` cũ.
- Giao diện đọc token thẳng từ `.standards/tokens/` (QU-STD-1); xóa `tokens/` và bản sao quy ước cũ trong `docs/` (QU-STD-2).
- README theo nhận diện tsudev, ghi hạng sản phẩm C.
- Cửa sổ xem trước hiển thị **nhãn vCard** (Tên, SĐT, Email...) thay cho tên cột CSV, thêm cột `Dòng CSV` và dòng chú thích cột CSV nguồn (`src/features/preview/columns.py`, 6 test).
- Tự động hóa kiểm thử GUI: `tests/test_gui_smoke.py` + `scripts/test-gui-win.ps1` chạy đúng kịch bản `docs/ARCHITECTURE.md` mục 8 (5 test); máy không có màn hình thì tự bỏ qua. Workflow phát hành chạy luôn phần này trên `windows-latest`.
- Sửa lỗi tiềm ẩn: thread chuyển đổi gọi `root.after` trực tiếp (tkinter không an toàn đa luồng) → chuyển sang hàng đợi do main thread rút, hủy lượt hẹn khi đóng cửa sổ.
- Thêm `scripts/sign-win.ps1`: ký Authenticode + đóng dấu thời gian bằng công cụ có sẵn của Windows (không tốn phí); `scripts/build-win.ps1` thêm cờ `-Sign` và tự ghi `release/SHA256SUMS.txt`.
- Repo chuyển sang **public** để GitHub Actions chạy miễn phí không giới hạn và ai cũng tải được bản phát hành.

## 26.8.2002 - 20/08/2026

- Thêm menu **Giao diện**: chủ đề Sáng / Ấm / Tối đổi ngay lúc chạy, ghi nhớ trong `settings.json` ở thư mục tạm (`src/services/settings.py`, 5 test).
- Chủ đề ấm/tối chuyển ttk theme sang `clam` và tô lại Entry/Combobox/Button/Treeview/Progressbar/Scrollbar từ tokens; ô nhật ký đổi `ScrolledText` → `Text` + `ttk.Scrollbar` (thanh cuộn cổ điển không đổi màu được trên Windows).
- Sửa lỗi nút "BẮT ĐẦU CHUYỂN ĐỔI" mất chữ trên Windows (theme `vista` bỏ qua nền của nút ttk) - chuyển sang `tk.Button` dùng màu từ tokens.
- Đoán cột CSV thông minh hơn: `converter.guessHeader` + `FIELD_ALIASES` (Anh/Việt, bỏ dấu, khớp `Phone 1 - Value` kiểu Google Contacts); trước đây trường bắt buộc SĐT luôn phải chọn tay.
- Chạy thử GUI thật trên Windows (Python 3.11) cho cả 3 chủ đề: 3 màn hình hiệu ứng → chuyển đổi 30 dòng → 20 vCard → cửa sổ xem trước hiển thị đúng, dòng lỗi tô đỏ.
- Chuẩn hóa tên bản phát hành theo `docs/DESIGN_SYSTEM.md` mục 6: `APP_VERSION` 5.2 → `26.8.2001`; `Contacts.spec` chuyển sang gói 1-file, xuất `tsudev-contact_26.8.2001_x64-setup.exe`.
- Thêm `scripts/build-win.ps1`: cài phụ thuộc → chạy test → PyInstaller → đưa sản phẩm vào `release/`.
- Chuẩn hóa repo theo bộ quy ước v1.0.0: khởi tạo git, ignore dữ liệu danh bạ PII, bổ sung `CHANGELOG.md` / `docs/ARCHITECTURE.md` / `.env.example`.
- Tách `contacts.pyw` (455 dòng) thành `src/` theo `docs/PROJECT_STRUCTURE.md`; `contacts.pyw` giữ vai trò điểm khởi chạy mỏng.
- Toàn bộ màu/cỡ chữ/spacing của giao diện lấy từ `tokens/design-tokens.json` qua `src/services/tokens.py` (hết hard-code).
- Sửa 3 lỗi: `sqlite3.Row.get()` làm hỏng hoàn toàn chức năng xuất VCF và cửa sổ xem trước; sai số tham số `_update_progress`; rò rỉ kết nối SQLite. Chi tiết: `docs/ARCHITECTURE.md` mục 6.
- CSDL tạm chuyển sang thư mục temp của người dùng (thư mục cài đặt có thể chỉ-đọc, và file đó chứa PII).
- Thêm `tests/test_csv_to_vcf.py` - 8 test tích hợp luồng CSV → SQLite → vCard.

## Ghi chú phát hành

- `26.8.2001` là bản build nội bộ đầu tiên theo quy ước tên mới, **không phát hành** (bị thay bởi 26.8.2002 trong cùng ngày sau khi thêm chủ đề + sửa lỗi giao diện).
- Các bản build trước 20/08/2026 dùng tên `Contacts.exe` (không theo quy ước).
