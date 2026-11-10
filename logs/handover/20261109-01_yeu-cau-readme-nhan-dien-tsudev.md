# PHIẾU YÊU CẦU - README theo nhận diện tsudev (ECOSYSTEM_IDENTITY mục 2.1)

- **Mã phiếu**: 20261109-01
- **Từ**: phiên tsudev-files-c2 (repo `tsudev-files`) - **Đến**: phiên sau của repo này
- **Thời điểm**: 21:26 09/11/2026
- **Trạng thái**: ĐÃ XỬ LÝ (mục 3 làm cùng website)
- **Ủy quyền**: chủ dự án đồng ý chuẩn hóa nhận diện mọi repo hệ tsudev (chat 09/11/2026, phiên tsudev-files).

## Đã làm hộ (trên GitHub, không đụng mã repo này)

- Mô tả repo kết thúc bằng ` | tsudev.com`, `homepage` = `https://tsudev.com` (chưa có trang sản phẩm riêng),
  thêm nhãn `tsudev`. Kiểm: `gh api repos/<owner>/<repo> --jq '.description,.homepage,.topics'`.

## Việc cần làm ở repo này

1. `README.md` mở đầu: dấu hiệu thu gọn, tên sản phẩm, một câu mô tả, rồi dòng
   `Một sản phẩm của [tsudev](https://tsudev.com).` (`.standards/docs/ECOSYSTEM_IDENTITY.md` mục 2.1).
2. Ghi **hạng sản phẩm** A/B/C vào README (`.standards/docs/AUTH_AND_ACCOUNT.md` mục 1). Lưu ý: bảng ví dụ ở mục 1 ghi `tsudev-contact` là hạng A (web có tài khoản), nhưng repo này là công cụ desktop chuyển CSV sang vCard - xác định lại cho đúng.
3. Khi repo `tsudev` làm xong trang sản phẩm (phiếu `tsudev/logs/handover/20261109-06_*`), đổi `homepage`
   sang trang đó.

## Kết quả xử lý

- 10/11/2026, agent-contact, nhánh `chore/don-nen-nhan-dien-tsudev`: xong mục 1 (README mở đầu dấu hiệu + dòng
  `Một sản phẩm của tsudev`) và mục 2 (**hạng C**: công cụ desktop ngoại tuyến, không tài khoản; đề xuất sửa bảng
  mục 1 của AUTH_AND_ACCOUNT gửi sang `tsudev-standards`).
- Mục 3: trang sản phẩm `contact.tsudev.com` do chính repo này dựng (thư mục `website/`), xong thì đổi `homepage`.
