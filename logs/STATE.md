# STATE.md - Trạng thái project (agent đọc đầu phiên, cập nhật cuối phiên)

## Hàng đợi task (làm từ trên xuống)
- [ ] Chủ project chọn giấy phép mã nguồn (repo public nhưng chưa có `LICENSE` = mặc định giữ mọi quyền).
- [x] **QU-STD-AUTH** XONG 11/11/2026: bộ quy ước v3.4.0 (TS-15) xếp repo này hạng C; hạng C không bắt buộc đăng nhập, app chạy trọn ngoại tuyến không tài khoản (`.standards/docs/AUTH_AND_ACCOUNT.md` mục 1).

### Gợi ý (chưa phải task)
- Xóa chứng thư thử nghiệm tự ký còn sót trong kho tin cậy của Windows (phiếu 20260820-03).
- Muốn hết cảnh báo SmartScreen phải mua chứng thư OV/EV.
- Trình cài đặt (shortcut Start Menu, gỡ cài đặt) nếu người dùng cần.

## Đang thực hiện
| Task | Agent | Bắt đầu |
|---|---|---|

## Đã hoàn thành (mới nhất trên cùng)
- 10/11/2026 - Phiếu `20261110-05` (giao diện đen + tím kiểu Supabase): website + app PySide6 chỉ Sáng/Tối/Hệ thống, mặc định Tối; màu riêng ở `tokens/extensions.tsudev-contact.json`. Chi tiết: mục Kết quả của phiếu.
- 10/11/2026 - Kết phiên: nhả khóa (commit nhả khóa trước đó bị mất khi tạo lại nhánh website), phiếu bàn giao `20261110-02`.
- 10/11/2026 - Merge #9, #13 (thay #10 bị GitHub tự đóng khi xóa nhánh base), #11, #12; phát hành **v26.11.1001** (Actions: test, build, SBOM, attestation đều đạt; đã tải về kiểm SHA-256 + `gh attestation verify` + chạy thật trên Windows); deploy **https://contact.tsudev.com** (9 trang 200, header bảo mật đủ, HTTP->HTTPS 301); `homepage` repo đổi sang trang này; bật ruleset "Bảo vệ main" (id 26943513, 4 check bắt buộc); merge Dependabot #14 (setup-python v7.1.0, đã đối chiếu SHA) và #16 (playwright 1.65); gửi phiếu `tsudev/logs/handover/20261110-04_*`.
- 10/11/2026 - Nâng cấp toàn diện (4 PR xếp chồng, CI xanh): PR #9 bỏ Facebook, nhận diện tsudev, QU-STD-1/2/BRAND (icon), README hạng C; PR #10 PySide6 + lõi `src/engine` (vá chèn vCard, PII chỉ trong RAM, trần đầu vào, chuẩn hóa SĐT VN), i18n vi/en, QU-STD-TABLE, 84 test, khóa hash, SBOM; PR #11 CI (ruff, pytest Linux+Windows, pip-audit, gitleaks), attestation, Dependabot; PR #12 website contact.tsudev.com (chưa deploy - chờ bản phát hành mới)
- 20/08/2026 - T14: repo chuyển **public**; Actions hết bị chặn, chạy trọn pipeline xanh (run `32291387041`); sửa 2 lỗi workflow (cache pip thiếu requirements.txt, đối chiếu tag khi chạy tay)
- 20/08/2026 - T13 `8470ceb`: `scripts/sign-win.ps1` ký Authenticode + dấu thời gian miễn phí, `build-win.ps1` thêm `-Sign` và tự ghi `release/SHA256SUMS.txt`
- 20/08/2026 - T12 `f528c3a`: `tests/test_gui_smoke.py` + `scripts/test-gui-win.ps1` tự động hóa kịch bản GUI (5 test, chạy thật trên Windows và trên runner CI); phát hiện & sửa lỗi gọi `root.after` từ thread nền
- 20/08/2026 - T11 `4eed8a5`: cửa sổ xem trước dùng nhãn vCard + cột `Dòng CSV` + chú thích cột CSV nguồn (6 test)
- 20/08/2026 - T10: push `main` lên repo private; tạo Release `v26.8.2002` kèm `.exe` + `SHA256SUMS.txt`; thêm workflow tự build khi đẩy tag
- 20/08/2026 - T9: chủ đề Sáng/Ấm/Tối + `src/services/settings.py` (ghi nhớ lựa chọn), 18/18 test
- 20/08/2026 - T8 `a47aa98`: chạy thử GUI thật trên Windows → phát hiện & sửa 2 lỗi (nút mất chữ, đoán cột CSV)
- 20/08/2026 - Build thật: `release/tsudev-contact_26.8.2002_x64-setup.exe` (18.5 MB), đã chạy thử file .exe
- 20/08/2026 - T7: thêm `scripts/build-win.ps1` (deps → test → PyInstaller → `release/`)
- 20/08/2026 - T6: chuẩn hóa tên phát hành - `APP_VERSION=26.8.2001`, `RELEASE_BASENAME` trong `src/app_info.py`, `Contacts.spec` gói 1-file
- 20/08/2026 - T5: tạo repo private `tsudev-tsudev/tsudev-contact`, push `main` (không file PII nào được theo dõi)
- 20/08/2026 - T3+T4 `b947660`: tách `contacts.pyw` → `src/`, giao diện dùng `tokens/`, thêm 8 test, sửa 3 lỗi
- 20/08/2026 - T2 `332c74d`: thêm CHANGELOG / ARCHITECTURE / .env.example, viết lại README
- 20/08/2026 - T1 `5032a7f`: `git init`, ignore dữ liệu danh bạ PII
- 19/08/2026 - Khởi tạo bộ quy ước v1.0.0

## Quyết định quan trọng
- 10/11/2026 - **PR xếp chồng**: merge PR dưới với `--delete-branch` làm GitHub ĐÓNG (không đổi base) PR phía trên. Cách đúng: merge không xóa nhánh -> `gh pr edit <trên> --base main` -> mới xóa nhánh; đồng bộ bằng `git merge origin/main` (không rebase/force-push).
- 10/11/2026 - Ruleset `main`: bắt buộc PR + 4 check (`Lint + test (Linux)`, `Test (Windows)`, `Quét lộ bí mật (gitleaks)`, `Kiểm quy ước`), nhánh phải cập nhật với main, giải quyết hết hội thoại; admin chỉ bypass qua PR (giống tsudev-files).
- 10/11/2026 - **Giao diện PySide6-Essentials** thay tkinter (exe ~26 MB); lõi `src/engine` thuần Python. Tên `engine` vì `.gitignore` chuẩn chặn đường dẫn `core`.
- 10/11/2026 - **Ngoại tuyến 100%**: không tự kiểm tra cập nhật, QtNetwork bị loại khỏi bản đóng gói. Hạng sản phẩm C.
- 10/11/2026 - **Danh bạ chỉ trong RAM**; settings ở `%LOCALAPPDATA%\tsudev-contact`; khởi động xóa `contacts_data.db` bản cũ để lại trong %TEMP%.
- 10/11/2026 - Website `contact.tsudev.com` = tên miền con 1 cấp, cùng khung Astro + Cloudflare Workers với files.tsudev.com, nằm trong `website/` của repo này.
- 10/11/2026 - Phụ thuộc: sửa `requirements*.in` rồi `scripts/lock-deps.sh` (uv `--universal --generate-hashes`); mọi nơi cài bằng `--require-hashes`.
- 20/08/2026 - **Repo đã chuyển PUBLIC** theo yêu cầu chủ project. Hệ quả đã kiểm chứng: GitHub Actions chạy lại bình thường (hết lỗi chặn thanh toán), phút Actions miễn phí không giới hạn, trang Releases ai cũng tải được. Toàn bộ project không dùng dịch vụ trả phí nào.
- 20/08/2026 - **Ký số**: chỉ dùng công cụ miễn phí có sẵn của Windows (`Set-AuthenticodeSignature` + timestamp RFC3161). Chứng thư tự ký KHÔNG gỡ được SmartScreen trên máy khác - chấp nhận, thay bằng đối chiếu `SHA256SUMS.txt`. Không mua chứng thư OV/EV.
- 20/08/2026 - Workflow **không bật `cache: pip`**: repo không có `requirements.txt` (phụ thuộc khai báo trong `scripts/build-win.ps1`); thêm file chỉ để cache là trùng lặp không đáng, repo public nên không cần tiết kiệm phút.
- 20/08/2026 - **tkinter không an toàn đa luồng**: mọi cập nhật UI từ thread nền phải qua `queue.Queue` do main thread rút (`ContactsApp._pumpUiQueue`), tuyệt đối không gọi `root.after` từ thread khác.
- 20/08/2026 - Phát hành qua **GitHub Releases**, tag `v<APP_VERSION>` (ví dụ `v26.8.2002`). Workflow chỉ chạy theo tag để tiết kiệm phút Actions; runner `windows-latest` tính 2x phút.
- 20/08/2026 - Repo giữ **private**: trang Releases chỉ mở được với tài khoản có quyền. Muốn ai cũng tải được thì phải chuyển repo sang public (chủ project quyết định).
- 20/08/2026 - **Cách chạy GUI/build Windows từ WSL**: gọi `powershell.exe` (interop) dùng Python 3.11 sẵn có trên Windows, tạo venv trong `%TEMP%\tsudev-contact-build`. Không cần cài `python3-tk` trong WSL.
- 20/08/2026 - Chủ đề sáng giữ ttk theme `vista` (native đẹp); ấm/tối bắt buộc `clam` vì `vista` bỏ qua màu nền. Nút hành động chính dùng `tk.Button` để chắc chắn đủ tương phản.
- 20/08/2026 - `scripts/build-win.ps1` phải lưu **UTF-8 CÓ BOM**: PowerShell 5.1 đọc .ps1 không BOM theo ANSI → hỏng tiếng Việt, lỗi cú pháp.
- 20/08/2026 - Không thêm trình cài đặt (Inno/NSIS): `Contacts.spec` chuyển sang **gói 1-file**, chính file `.exe` đó là bản `-setup.exe` theo quy ước. Thêm installer chỉ khi cần shortcut/uninstaller.
- 20/08/2026 - `src/app_info.py` là nguồn duy nhất của tên bản phát hành (`RELEASE_BASENAME`); spec và script build đều đọc từ đó. Bản kế tiếp trong ngày chỉ cần tăng `NN`.
- 20/08/2026 - `src/` dùng `snake_case` cho file/thư mục (Python không import được dấu gạch ngang); hàm/biến giữ `camelCase`.
- 20/08/2026 - Logic chuyển đổi tách khỏi tkinter, giao tiếp qua callback → test được không cần màn hình.
- 20/08/2026 - Giao diện đọc thẳng `tokens/design-tokens.json` qua `src/services/tokens.py`; cỡ chữ truyền tkinter dạng số âm = pixel.
- 20/08/2026 - CSDL tạm đặt ở thư mục temp người dùng, không đặt cạnh file thực thi (chỉ-đọc + chứa PII).
- 19/08/2026 - Dùng Inter làm font chuẩn; token là nguồn chân lý duy nhất; region ưu tiên Singapore → Nhật Bản.
