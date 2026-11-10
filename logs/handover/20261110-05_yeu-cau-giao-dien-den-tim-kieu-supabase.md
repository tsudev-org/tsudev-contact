# PHIẾU YÊU CẦU - Giao diện đen tuyền + tím, bố cục kiểu Supabase, chỉ Sáng / Tối / Hệ thống

- **Mã phiếu**: 20261110-05
- **Từ**: phiên 47 của repo `tsudev` (tsudev.com) - **Đến**: phiên kế tiếp của repo `tsudev-contact`
- **Thời điểm**: 10/11/2026
- **Trạng thái**: ĐÓNG (mã + kiểm thử xong 10/11/2026; deploy website và phát hành app ghi ở mục Kết quả)
- **Tham chiếu**: tsudev.com đã làm trước - nhánh `feat/giao-dien-tim-den-supabase` của `tsudev-org/tsudev`
  (`tokens/extensions.tsudev-web.json`, `packages/ui/src/components/ThemeToggle.tsx`, `SiteFooter.tsx`,
  `apps/frontend-main/styles/globals.css`, `apps/frontend-main/pages/_document.tsx`). Đọc các tệp đó trước khi
  tự dựng - chép HÀNH VI, đừng chép mã React nếu site của bạn không dùng React.

## 0. Riêng cho repo `tsudev-contact`

- Website contact.tsudev.com (Astro, cùng khung với files.tsudev.com, lên 10/11/2026): chưa có phiếu nút giao
  diện nào - làm thẳng theo phiếu này. Phối hợp với phiên tsudev-files (cùng khung) để không lệch nhau.
- **tsudev-files đã làm xong trước** (PR tsudev-org/tsudev-files#29, 10/11/2026) trên CÙNG khung Astro - chép theo:
  `website/public/theme.js` (tệp cùng nguồn, CSP `script-src 'self'`, không băm nội tuyến),
  `src/styles/palette.css`, `src/styles/site.css`, phần footer của `src/layouts/Trang.astro`, và
  `scripts/check-theme.mjs` (Chromium với CSP production).
- App PySide6: nếu có tuỳ chọn giao diện, chỉ còn Sáng / Tối / Hệ thống (Qt: `QStyleHints.colorScheme()` cho
  "Hệ thống"), màu nhấn theo bảng §2.
- tsudev.com đã trỏ thẻ tsudev-contact tới https://contact.tsudev.com (việc 2 của phiếu 20261110-04 - xong).

## 1. Quyết định của chủ dự án (10/11/2026) - áp cho TOÀN hệ sinh thái

1. **Tông màu chủ đạo: ĐEN TUYỀN + TÍM TƯƠI.** Thay tông đen + xanh dương/xanh lá của phiên 46. Xám trung tính
   cho mọi bề mặt, tím CHỈ ở điểm nhấn (nút chính, liên kết, một quầng sáng tĩnh ở đỉnh trang).
2. **Bố cục, nút, hiệu ứng tham khảo https://supabase.com** (không chép logo/chữ/ảnh của Supabase - chỉ học
   ngôn ngữ thiết kế): nền LIỀN MẠCH, không dải nền khác màu giữa các khối, không khung đứt đoạn.
3. **Chỉ BA lựa chọn giao diện: Sáng / Tối / Hệ thống** (như supabase.com). **Bỏ chế độ Ấm** ở mọi nơi.
   Mặc định cho khách mới là **Tối**; "Hệ thống" là lựa chọn người dùng tự bật.
4. **Chân trang**: hàng cuối cùng là `© tsudev` (bên trái) + **bộ chọn giao diện** (bên phải). Nút đổi giao
   diện **chuyển từ header xuống chân trang** - phiếu `20261110-02/03` (nút Sáng/Tối ở header) được THAY bởi
   phiếu này: nếu chưa làm phiếu đó thì làm thẳng theo phiếu này; nếu đã làm thì dời nút xuống footer và thêm
   lựa chọn "Hệ thống".
5. Icon không được trùng màu với nền chỗ chứa nó; trang tải/giới thiệu app phải có biểu tượng app.

## 2. Bảng màu chuẩn (đã áp ở tsudev.com, PR `feat/giao-dien-tim-den-supabase`; mọi cặp đạt WCAG AA)

| Vai trò            | Tối (mặc định)             | Sáng                        |
| ------------------ | -------------------------- | --------------------------- |
| nền trang          | `#0A0A0A` (KHÔNG `#000`)   | `#FAFAFA`                   |
| bề mặt (card)      | `#111111`                  | `#FFFFFF`                   |
| bề mặt lồng        | `#171717`                  | `#F4F4F5`                   |
| hover              | `#1F1F1F`                  | `#EBEBED`                   |
| viền hairline      | `#242424`                  | `#E4E4E7`                   |
| viền đậm           | `#2E2E2E`                  | `#D4D4D8`                   |
| viền ô nhập/nút    | `#6E6E6E`                  | `#71717A`                   |
| chữ chính          | `#EDEDED`                  | `#0A0A0A`                   |
| chữ phụ            | `#B4B4B4`                  | `#3F3F46`                   |
| chữ mờ             | `#8F8F8F`                  | `#52525B`                   |
| liên kết           | `#C4A1FF`                  | `#6D28D9`                   |
| primary (nút chính)| `#A970FF`                  | `#7C3AED`                   |
| primary hover      | `#BB8CFF`                  | `#6D28D9`                   |
| primary active     | `#9A5CF5`                  | `#5B21B6`                   |
| chữ trên primary   | `#0A0A0A` (mực đen!)       | `#FFFFFF`                   |
| vòng focus         | `#A970FF`                  | `#7C3AED`                   |
| nhấn phụ (accent)  | `#E879F9`                  | `#A21CAF`                   |
| quầng sáng (glow)  | `rgba(169,112,255,0.16)`   | `rgba(124,58,237,0.10)`     |

⚠️ Ở chế độ Tối chữ trên nút tím là **mực đen**, không phải trắng: không mã tím nào vừa đạt 4.5:1 làm chữ trên
nền `#0A0A0A` vừa đạt 4.5:1 dưới chữ trắng (đã tính - hai ngưỡng độ sáng không giao nhau). Đừng "sửa" thành
chữ trắng.

`<meta name="theme-color">`: Tối `#0a0a0a`, Sáng `#fafafa`. `site.webmanifest`: `theme_color`/`background_color`
= `#0a0a0a`.

## 3. Bộ chọn giao diện - hợp đồng hành vi (khớp tsudev.com)

- Khoá localStorage: `tsudev-theme`, giá trị `light` | `dark` | `system`. Giá trị cũ `warm` ⇒ đọc thành
  `light` (người từng chọn Ấm muốn nền sáng). Không có/không đọc được ⇒ `dark`.
- Áp TRƯỚC KHI VẼ bằng script đồng bộ nội tuyến trong `<head>`, đặt SAU `<meta name="theme-color">` và TRƯỚC
  stylesheet (bài học cwico: đặt trước meta thì không đổi được màu thanh địa chỉ). Script đặt
  `data-theme="light|dark"` lên `<html>` và đổi `content` của meta theme-color. `system` ⇒ hỏi
  `matchMedia('(prefers-color-scheme: dark)')` và nghe sự kiện `change` khi đang chọn `system`.
- CSS KHÔNG được treo bảng màu vào `@media (prefers-color-scheme)` - chỉ JavaScript được hỏi hệ điều hành.
- Giao diện: nhóm 3 nút biểu tượng (mặt trời / mặt trăng / màn hình) bo tròn, `role="radiogroup"`
  `aria-label="Giao diện"`, mỗi nút `role="radio"` + `aria-checked` + `aria-label` (Sáng / Tối / Hệ thống),
  phím ← → chuyển lựa chọn. Nút đang chọn nền `hover`, chữ chính; nút khác chữ mờ.
- CSP: script nội tuyến cần băm `sha256-...` trong `script-src` (hoặc file `.js` cùng origin nếu CSP
  `default-src 'none'` không có `script-src`). Đổi nội dung script ⇒ đổi băm. KHÔNG nới thành `'unsafe-inline'`.

## 4. Ngôn ngữ thiết kế kiểu Supabase - danh sách kiểm

- [ ] MỘT nền liền mạch từ header tới footer: bỏ mọi dải nền khác màu (hero, đầu trang con, footer), bỏ viền
      ngang cắt trang; ranh giới giữa các khối là khoảng trống.
- [ ] Header dính, kính mờ trên CÙNG màu nền trang + một đường hairline dưới; link điều hướng chữ phụ → chữ
      chính khi hover/đang ở trang; bên phải: nút phụ + nút chính cao 32px.
- [ ] Nút chính: nền primary + viền primary-hover 1px, bo 6px, chữ `font-medium` 14px. Nút phụ: nền bề mặt +
      viền đậm, hover viền ô nhập + nền hover. Không quầng sáng quanh nút, không gradient trên nút.
- [ ] Thẻ: nền bề mặt + viền hairline, bo 8px; hover = viền đậm lên + nền sáng hơn một bậc. Không nhấc, không
      quầng màu, không viền chuyển sắc.
- [ ] Hero canh giữa, tiêu đề `font-semibold` (không extrabold), một cụm chữ tím → tím hồng tĩnh; quầng tím tĩnh
      phía sau. Không aurora/chuyển động nền, không ánh trượt.
- [ ] Nhãn nhỏ (eyebrow) kiểu mono chữ hoa màu liên kết, không phải viên thuốc có nền.
- [ ] **Icon trong nút/ô nền đặc ăn màu chữ của nút** (`currentColor`), không mang màu vai trò riêng - icon xanh
      lá/ngọc trên nút tím chính là lỗi "icon lẫn vào nền" chủ dự án báo.
- [ ] Biểu tượng app: glyph nét 1.6 trên ô bo 8px nền tím nhạt (`primary` 10% trộn bề mặt) + viền tím mờ, glyph
      màu liên kết. Chênh glyph/nền ≥ 4.5:1 ở cả hai chế độ.
- [ ] Chân trang: các cột liên kết chữ mờ → chữ chính khi hover; hàng cuối `© tsudev` + bộ chọn giao diện.
- [ ] Giữ nguyên: câu mô tả chuẩn ECOSYSTEM_IDENTITY §1, liên kết qua lại giữa các site, font tự host.

## 5. Nghiệm thu

1. Tương phản AA ở CẢ HAI chế độ (chữ 4.5:1, viền/focus 3:1).
2. Chọn Sáng → tải lại → vẫn Sáng; chọn Hệ thống → đổi chế độ máy → trang đổi theo không cần tải lại.
3. Không còn chuỗi/lựa chọn "Ấm" trong giao diện.
4. Production: CSP không chặn script chọn giao diện (console 0 lỗi), `theme-color` đúng màu từng chế độ.
5. Ghi kết quả vào mục "Kết quả xử lý" cuối phiếu này, đổi trạng thái ĐÓNG, rồi báo lại repo `tsudev`
   (phiếu báo kết quả trong `tsudev/logs/handover/` hoặc nhắn phiên tsudev).

## Kết quả xử lý

Phiên projects-0c, 10/11/2026, nhánh `feat/giao-dien-den-tim-supabase`. Chép theo tsudev-files PR #29 (hợp ba
chiều từng tệp, không chép mù).

- **Website** (§2-§4): `website/src/styles/palette.css` (bảng §2, ghi đè `tokens.css` bản sao standards),
  `public/theme.js` (CSP `script-src 'self'`, không nội tuyến, nạp chặn sau meta theme-color), bộ chọn radiogroup
  Sáng/Tối/Hệ thống ở hàng cuối chân trang cạnh `© tsudev`, header kính mờ + nút "Mã nguồn"/"Tải về" 32px, nền liền
  mạch (bỏ `muc--nen`), hero canh giữa có cụm chữ tím, nhãn mono; manifest `#0a0a0a`. Ảnh app trên site chụp lại
  bằng `tools/chup_anh_web.py` (`QWidget.grab()`, dữ liệu mẫu).
- **Lỗi bắt được**: trang `/huong-dan/` có `<h2 id="giao-dien">` trùng id với bộ chọn - `theme.js` sẽ gắn nhầm. Đổi
  thành `giao-dien-ngon-ngu`.
- **App PySide6**: chỉ Sáng/Tối/Hệ thống, mặc định Tối, `warm` cũ trong `settings.json` -> Sáng; màu ghi đè ở
  `tokens/extensions.tsudev-contact.json` (vai trò lạ -> dừng sớm), đóng gói qua `Contacts.spec`. "Hệ thống" dùng
  `QStyleHints.colorScheme()` + `colorSchemeChanged` (đã có).
- **Kiểm**: pytest 86/86 (thêm test mặc định Tối/`warm`, test tương phản AA cả hai chế độ), ruff sạch,
  `check-standards.sh` đạt, `check-dist` 0, `check-theme` 0 (Chromium + CSP production), `check-a11y` 9 trang x 2
  chế độ 0 lỗi; xem ảnh chụp 1440/390px cả hai chế độ: không tràn ngang, footer đúng.
