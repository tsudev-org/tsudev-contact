# Website contact.tsudev.com

Trang sản phẩm của tsudev-contact. Khung dùng chung với `files.tsudev.com`: [Astro](https://astro.build) dựng trang
tĩnh; JavaScript phía trình duyệt chỉ có `public/theme.js` (nút đổi giao diện Sáng/Tối/Hệ thống ở chân trang, mặc định Tối, khóa
`tsudev-theme` như tsudev.com); host trên Cloudflare Workers Static Assets (Worker `tsudev-contact`, không có mã
chạy; tên miền con `contact.tsudev.com`, cấu hình ở `wrangler.jsonc`).

* Tài liệu lấy trực tiếp từ tệp của repo (`SECURITY.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`,
  `THIRD-PARTY-NOTICES.md`) - sửa ở đó, không sửa trong `website/`. Trang Hướng dẫn, Chuẩn bị CSV, Tải về viết tay
  trong `src/pages/`.
* Bản phát hành (phiên bản, liên kết, SHA-256) lấy từ GitHub Releases lúc build.
* Ảnh chụp `public/anh/ung-dung-*.png` render từ chính ứng dụng (`QWidget.grab()`, dữ liệu giả của
  `tests/fixtures/make_samples.py`), không chụp màn hình thật.
* Tài sản thương hiệu (`favicon*`, `android-chrome-*`, `og-image.png`, `brand/`) sinh bằng `scripts/brand-assets.mjs` từ MỘT ảnh gốc `assets/brand/source/` (cấu hình `assets/brand/brand.json`); không sửa tay - đổi logo: thay ảnh gốc rồi `node website/scripts/brand-assets.mjs`, CI chạy `--check`.
  từ dây chuyền thương hiệu của repo `tsudev-org/tsudev`; không sửa tay.
* Header bảo mật (HSTS, CSP `default-src 'none'`, `X-Frame-Options: DENY`...) ở `public/_headers`; `security.txt` ở
  `public/.well-known/`. `scripts/check-dist.mjs` chạy sau mỗi lần build.

```bash
cd website
npm ci
npm run dev          # http://localhost:4321
npm run build        # dựng vào dist/ và kiểm tra
npm run check:a11y   # axe-core WCAG 2.2 AA, Sáng + Tối (lần đầu: npx playwright install chromium)
npm run check:theme  # nút đổi giao diện với CSP của production
npm run deploy       # build rồi `wrangler deploy` (cần `npx wrangler login` với tài khoản tsudev)
```

Sau mỗi lần phát hành bản mới, chạy lại `npm run deploy` để trang Tải về cập nhật phiên bản và mã SHA-256.
