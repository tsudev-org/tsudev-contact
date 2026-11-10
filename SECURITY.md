# Chính sách bảo mật - tsudev-contact

## Báo lỗ hổng

**KHÔNG mở issue công khai.** Dùng [Báo cáo lỗ hổng riêng tư của GitHub](https://github.com/tsudev-org/tsudev-contact/security/advisories/new).
Vui lòng gửi: phiên bản, cách tái hiện (tệp CSV mẫu **không chứa dữ liệu thật**), tác động.

Cam kết phản hồi trong 7 ngày, bản sửa cho lỗi nghiêm trọng trong 30 ngày. Quy trình chung của hệ
sinh thái: [`.standards/SECURITY.md`](.standards/SECURITY.md).

## Phạm vi

Ứng dụng chạy ngoại tuyến, không tài khoản, không kết nối mạng. Mô hình mối đe dọa và biện pháp
đang áp dụng: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) mục 5.

## Kiểm chứng bản tải về

Mỗi bản phát hành kèm `SHA256SUMS.txt`, SBOM `*.cdx.json` và chứng thực nguồn gốc bản build:

```bash
gh attestation verify tsudev-contact_<phiên-bản>_x64-setup.exe --repo tsudev-org/tsudev-contact
```
