# PHIẾU YÊU CẦU - Thêm `scoop` vào `channels` (gói Scoop `tsudev-contact` đã có)

- **Mã phiếu**: 20261113-02
- **Từ**: phiên `linux-packages-1e` (phần Scoop của phiếu toàn hệ `~/projects/logs/handover/20261113-01` mục 2.2)
- **Đến**: phiên repo `tsudev-contact`
- **Thời điểm**: 13/11/2026
- **Trạng thái**: ĐÓNG mục 1 (13/11/2026); mục 2 (tuỳ chọn) để lại

## 1. Đã có

`scoop install tsudev/tsudev-contact` (sau `scoop bucket add tsudev https://github.com/tsudev-org/scoop-bucket`) -
tsudev-org/scoop-bucket PR #4, CI cài thật trên Windows xanh. Bucket dùng `tsudev-contact_<v>_x64-setup.exe`, đổi tên
thành `tsudev-contact.exe` (bản PyInstaller một tệp), mã băm từ `SHA256SUMS.txt` của Release; `excavator` tự cập nhật khi
có Release mới. Vì vậy **giữ tên tệp và giữ `SHA256SUMS.txt`** ở các Release sau.

## 2. Việc cần làm

1. `packaging/package.json`: thêm `"scoop"` vào `channels`, giữ `winget` trong `planned`.
2. (Nên) đổi `assets.windows-x64.file` sang tên không có `setup` ở bản sau, vì tệp là app chạy thẳng chứ không phải bộ
   cài. Nếu đổi thì báo phiên linux-packages / scoop-bucket để sửa `autoupdate` cùng lúc.

## 3. Kết quả xử lý (phiên nhận điền)

- 13/11/2026 - phiên tsudev-06 (repo tsudev, chủ dự án ủy quyền; repo không có phiên nào mở): mục 1 XONG - `channels`
  = `["scoop"]`, `planned` giữ `["winget"]`. tsudev.com/apps hiện lệnh Scoop (tsudev#233). Mục 2 (đổi tên tệp không có
  `setup`) CHƯA làm: cần một bản phát hành mới và sửa `autoupdate` của scoop-bucket cùng lúc - làm ở lần phát hành sau.
