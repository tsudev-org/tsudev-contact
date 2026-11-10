# ARCHITECTURE.md - Kiến trúc tsudev-contact

> Ghi một lần, các phiên sau tham chiếu file này thay vì đọc lại mã nguồn.
> Quy ước chung: `.standards/AGENTS.md`. Lịch sử bản tkinter (<= 26.8.2002): git log trước PR #10.

## 1. Mục đích

Công cụ desktop chuyển danh bạ **CSV -> vCard (.vcf)** để nạp vào điện thoại. Chạy ngoại tuyến
hoàn toàn, không tài khoản (**hạng C**), dữ liệu cao nhất **D2** (họ tên, số điện thoại, chức vụ).

## 2. Ngăn xếp

| Thành phần | Lựa chọn | Lý do |
| --- | --- | --- |
| Giao diện | PySide6-Essentials 6.12 (Qt 6, LGPL-3.0), style `Fusion` + QSS sinh từ token | Giao diện hiện đại, HiDPI chuẩn, đồng nhất mọi nền tảng; tkinter không đổi được nền nút ở theme `vista` |
| Font | Inter 4.1 nhúng trong `assets/fonts/` (OFL) | Token `font-family`, không phụ thuộc máy |
| Icon | Lucide (ISC), SVG nội tuyến tô màu theo token | DESIGN_SYSTEM mục 5 |
| Lưu trữ | Chỉ RAM | Không để dữ liệu cá nhân trên đĩa (bản cũ ghi SQLite vào %TEMP% và không xóa) |
| Đóng gói | PyInstaller 1 file, không UPX, loại module/plugin Qt không dùng (kể cả QtNetwork) | ~26 MB, bề mặt tấn công hẹp |
| Phụ thuộc | `requirements*.in` -> `requirements*.txt` khóa phiên bản + hash (`scripts/lock-deps.sh`, uv `--universal`) | SECURITY_BASELINE mục 5 |

## 3. Bố cục mã nguồn

```
src/
├── app_info.py             # tên, phiên bản, nhà phát hành, URL - nguồn duy nhất
├── engine/                 # THUẦN Python, không import Qt - test được không cần màn hình
│   ├── text.py             # làm sạch ô dữ liệu; viRemoveDiacritics / viNormalizeText (module duy nhất)
│   ├── csv_source.py       # đọc CSV phòng thủ: trần kích thước, nhận bảng mã + dấu phân cách
│   ├── fields.py           # danh mục trường vCard, trần độ dài, đoán cột
│   ├── validate.py         # chuẩn hóa SĐT/email/ngày sinh -> ContactRecord + Issue (mã lỗi)
│   ├── vcard.py            # thoát ký tự RFC 6350, gập dòng 75 octet, CRLF, ghi nguyên tử
│   └── pipeline.py         # validateRows / exportVcf / exportIssueReport, CancelToken
├── i18n/                   # vi.py (mặc định, nguồn chuẩn) + en.py; tr(), formatNumber()
├── services/
│   ├── settings.py         # %LOCALAPPDATA%\tsudev-contact\settings.json, kiểm từng giá trị, ghi nguyên tử
│   └── tokens.py           # đọc .standards/tokens/design-tokens.json
├── ui/                     # PySide6
│   ├── main_window.py      # 3 bước: tệp -> ghép cột -> xem trước & xuất; Task nền + số thế hệ
│   ├── preview.py          # bảng theo DATA_TABLE.md: lọc trạng thái, tìm không dấu, 10/20/50/100/200
│   ├── mapping.py          # ghép cột + giá trị mẫu
│   ├── theme.py            # bảng màu + QSS từ token; 'system' theo hệ điều hành
│   ├── widgets.py          # Card, DropZone, Toast, Task (QRunnable)
│   ├── icons.py, about.py
└── main/app.py             # điểm vào; contacts.pyw chỉ gọi main()
```

Gói lõi tên `engine` (không phải `core`): bộ `.gitignore` chuẩn chặn mọi đường dẫn tên `core` (core dump).
Tên file/thư mục `snake_case` (Python không import được gạch ngang), hàm/biến `camelCase`.

## 4. Luồng dữ liệu

```
Tệp CSV (kéo-thả hoặc chọn)  --Task nền-->  readCsv: kích thước <= 50 MB, <= 100.000 dòng,
                                             <= 200 cột, ô <= 64 KB; UTF-8/UTF-16/Windows-1258
  -> guessMapping (tự ghép cột) -> người dùng chỉnh
  -> validateRows (Task nền, tự chạy lại 250 ms sau mỗi thay đổi ghép cột/tùy chọn)
       mỗi dòng -> ContactRecord: ok | warning (vẫn xuất) | error (không xuất)
  -> PreviewPanel (chỉ dựng 1 trang trong model)
  -> exportVcf: chỉ bản ghi không lỗi, ghi file tạm cùng thư mục rồi os.replace
  -> exportIssueReport (tùy chọn): CSV UTF-8 BOM, ô bắt đầu bằng = + - @ bị vô hiệu hóa
```

## 5. Kiến trúc bảo mật

| Mối đe dọa | Biện pháp | Test chặn |
| --- | --- | --- |
| Chèn vCard: ô chứa xuống dòng sinh liên hệ giả (đã khai thác được ở bản cũ) | `escapeValue` thoát `\ ; ,` và xuống dòng mọi trường, gập dòng không cắt UTF-8 | `test_core_vcard.py` (gồm test tính chất Hypothesis 300 mẫu) |
| Giả mạo tên bằng ký tự vô hình / đảo chiều chữ (Trojan Source) | `sanitizeField`: NFC, bỏ C0/C1, bỏ U+200B..U+202E, U+2066..U+2069... | `test_core_input.py` |
| Tệp độc làm cạn RAM / treo | Trần kích thước, số dòng, số cột, độ dài ô, độ dài từng trường | `test_tu_choi_*` |
| Tệp nhị phân / `.xlsx` đổi đuôi | Phát hiện byte NUL, báo rõ | `test_tu_choi_file_nhi_phan` |
| Mất dữ liệu lặng lẽ do bảng mã | Không còn `errors='ignore'`; báo bảng mã đã dùng | `test_nhan_bang_ma` |
| Chèn công thức khi mở báo cáo bằng Excel (CSV injection) | `csvSafe` thêm `'` trước `= + - @` (kể cả dạng full-width) | `test_xuat_bao_cao_vo_hieu_cong_thuc` |
| Dữ liệu cá nhân còn trên đĩa | Chỉ giữ trong RAM; xóa `contacts_data.db` bản cũ để lại khi khởi động | `test_xoa_csdl_tam_cua_ban_cu` |
| Ghi hỏng / ghi đè tệp nguồn | Ghi nguyên tử; chặn đích trùng tệp CSV nguồn; hộp thoại hỏi trước khi ghi đè | `test_loi_giua_chung_*`, `test_khong_ghi_de_tep_nguon` |
| settings.json bị sửa tay / hỏng | Chỉ nhận khóa biết trước, kiểm từng giá trị, trần 64 KB | `test_gia_tri_hong_*` |
| Mở URL lạ | Chỉ mở 3 URL cố định trong `app_info.py` (`openTrustedUrl`) | - |
| Dữ liệu CSV hiển thị như HTML | Nhãn hiển thị dữ liệu đặt `PlainText`; bảng dùng model, không render HTML | - |
| Chuỗi cung ứng | Khóa hash, `--require-hashes`, pip-audit, SBOM CycloneDX, action ghim SHA (PR CI) | CI |
| Đa luồng Qt | Thread nền chỉ phát Signal; kết quả tác vụ cũ bị bỏ nhờ `generation` | `test_ui.py` |

App **không mở kết nối mạng nào**: không có mã mạng, QtNetwork bị loại khỏi bản đóng gói.

## 6. Quy tắc dữ liệu

- Tệp danh bạ thật (`*.csv`, `*.vcf`, `*.db`) **không bao giờ vào git** - `.gitignore` chặn.
- Dữ liệu mẫu cho test/chụp giao diện: `python tests/fixtures/make_samples.py <thư-mục>` (tên/số giả).

## 7. Kiểm thử

```bash
python -m pytest -q tests                      # Linux/WSL: giao diện chạy offscreen
powershell -File scripts\test-gui-win.ps1      # Windows: venv riêng trong %TEMP%, cài theo hash
powershell -File scripts\test-gui-win.ps1 -Visible   # thấy cửa sổ thật
```

`tests/test_ui.py` đi trọn kịch bản: nạp CSV -> tự ghép cột -> lọc/tìm/đổi cỡ trang -> xuất vCard
(đọc lại bằng `tests/vcard_reader.py` độc lập) -> báo cáo lỗi -> đổi chủ đề/ngôn ngữ -> tệp hỏng.

## 8. Nợ kỹ thuật

1. Chưa có trình cài đặt (shortcut Start Menu, gỡ cài đặt) - bản phát hành là 1 file `.exe`.
2. Chưa có chứng thư ký số OV/EV - SmartScreen vẫn cảnh báo lần đầu; đối chiếu `SHA256SUMS.txt`
   và chứng thực nguồn gốc bản build (GitHub attestation) thay thế.
3. Đổi chủ đề áp lại QSS toàn app (~1 giây trên máy chậm) - chấp nhận được, tối ưu khi cần.
