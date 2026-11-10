// Kiểm tra bộ chọn giao diện trong Chromium thật, với CSP của production (phiếu logs/handover/20261110-05 mục 3, 5):
// mặc định Tối; 3 lựa chọn Sáng/Tối/Hệ thống giữ sau khi tải lại; "warm" cũ đọc thành Sáng; "Hệ thống" đổi theo máy
// không cần tải lại; data-theme có ngay từ khung hình đầu (không nháy màu); theme-color theo chế độ; localStorage bị
// chặn không làm hỏng trang; radiogroup (ARIA, phím mũi tên) ở chân trang; không lỗi CSP/console.
// Chạy sau `npm run build`: `npm run check:theme`.
import { chromium } from 'playwright';
import { moMayChu } from './may-chu-tinh.mjs';

const { base, dong } = await moMayChu();
const browser = await chromium.launch();
const loi = [];
const ky = (dk, mo) => { if (!dk) loi.push(mo); };
const NEN = { light: '#fafafa', dark: '#0a0a0a' };
const NEN_RGB = { light: 'rgb(250, 250, 250)', dark: 'rgb(10, 10, 10)' };
const NUT = (c) => `#giao-dien [data-chon-giao-dien="${c}"]`;

async function trang(context, theoDoi = true) {
  const page = await context.newPage();
  if (theoDoi) {
    page.on('console', (m) => { if (m.type() === 'error') loi.push(`console: ${m.text()}`); });
    page.on('pageerror', (e) => loi.push(`script: ${e.message}`));
  }
  return page;
}
const trangThai = (page) => page.evaluate(() => ({
  theme: document.documentElement.dataset.theme,
  chon: document.documentElement.dataset.themeChon,
  luu: (() => { try { return localStorage.getItem('tsudev-theme'); } catch { return 'LOI'; } })(),
  mau: [...document.querySelectorAll('meta[name="theme-color"]')].map((m) => m.content),
  nen: getComputedStyle(document.body).backgroundColor,
  checked: [...document.querySelectorAll('[data-chon-giao-dien]')].filter((b) => b.getAttribute('aria-checked') === 'true').map((b) => b.dataset.chonGiaoDien),
}));

// 1. Khách mới: Tối, kể cả khi máy đang ở chế độ sáng
for (const scheme of ['light', 'dark']) {
  const ctx = await browser.newContext({ colorScheme: scheme });
  const page = await trang(ctx);
  await page.goto(base + '/');
  const s = await trangThai(page);
  ky(s.theme === 'dark' && s.chon === 'dark' && s.nen === NEN_RGB.dark, `khách mới (máy ${scheme}): ${JSON.stringify(s)}`);
  ky(s.mau.length === 1 && s.mau[0] === NEN.dark, `theme-color khách mới: ${s.mau}`);
  ky(s.checked.join() === 'dark', `aria-checked khách mới: ${s.checked}`);
  ky(await page.locator('footer #giao-dien[role="radiogroup"]').isVisible(), 'bộ chọn không hiện ở chân trang');
  ky(await page.locator('header [data-chon-giao-dien], header #giao-dien').count() === 0, 'header vẫn còn nút giao diện');
  ky(!(await page.locator('body').innerText()).includes('Ấm'), 'còn chữ "Ấm" trong trang');
  await ctx.close();
}

// 2. Bấm từng lựa chọn: đổi ngay, lưu đúng khóa, giữ sau khi tải lại; data-theme có trước khi body được vẽ
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  await ctx.addInitScript(() => {
    new MutationObserver((ds, ob) => {
      if (document.body) { window.__themeKhiCoBody = document.documentElement.dataset.theme; ob.disconnect(); }
    }).observe(document, { childList: true, subtree: true });   // chạy trước khi có <html>: theo dõi cả document
  });
  const page = await trang(ctx);
  await page.goto(base + '/huong-dan/');
  for (const [chon, mongDoi] of [['light', 'light'], ['dark', 'dark'], ['system', 'light'], ['light', 'light']]) {
    await page.click(NUT(chon));
    let s = await trangThai(page);
    ky(s.theme === mongDoi && s.chon === chon && s.luu === chon && s.checked.join() === chon, `bấm ${chon}: ${JSON.stringify(s)}`);
    await page.reload();
    s = await trangThai(page);
    ky(s.theme === mongDoi && s.chon === chon && s.checked.join() === chon, `tải lại sau ${chon}: ${JSON.stringify(s)}`);
    ky(await page.evaluate(() => window.__themeKhiCoBody) === mongDoi, `${chon}: data-theme chưa có khi <body> bắt đầu (nháy màu)`);
    ky(s.mau.every((m) => m === NEN[mongDoi]) && s.nen === NEN_RGB[mongDoi], `màu sau ${chon}: ${s.mau} ${s.nen}`);
  }
  await ctx.close();
}

// 3. "Hệ thống" đổi theo máy không cần tải lại
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  const page = await trang(ctx);
  await page.goto(base + '/');
  await page.click(NUT('system'));
  ky((await trangThai(page)).theme === 'light', '"Hệ thống" với máy sáng không ra Sáng');
  await page.emulateMedia({ colorScheme: 'dark' });
  const doi = await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, { timeout: 3000 }).then(() => true, () => false);
  ky(doi, '"Hệ thống" không đổi sang Tối khi máy đổi');
  ky((await trangThai(page)).mau.every((m) => m === NEN.dark), 'theme-color không đổi theo máy');
  await page.click(NUT('light'));
  await page.emulateMedia({ colorScheme: 'light' });
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForTimeout(200);
  ky((await trangThai(page)).theme === 'light', 'đã chọn Sáng mà vẫn đổi theo máy');
  await ctx.close();
}

// 4. Giá trị cũ "warm" -> Sáng; giá trị lạ -> Tối
for (const [cu, mongDoi, chon] of [['warm', 'light', 'light'], ['"><img src=x>', 'dark', 'dark']]) {
  const ctx = await browser.newContext({ colorScheme: 'dark' });
  await ctx.addInitScript((v) => localStorage.setItem('tsudev-theme', v), cu);
  const page = await trang(ctx);
  await page.goto(base + '/');
  const s = await trangThai(page);
  ky(s.theme === mongDoi && s.chon === chon && s.checked.join() === chon, `localStorage "${cu}": ${JSON.stringify(s)}`);
  await ctx.close();
}

// 5. Bàn phím: chỉ nút đang chọn nằm trong thứ tự Tab; mũi tên chọn luôn nút kế bên, vòng quanh
{
  const ctx = await browser.newContext();
  const page = await trang(ctx);
  await page.goto(base + '/');
  ky(await page.evaluate(() => [...document.querySelectorAll('[data-chon-giao-dien]')].map((b) => b.tabIndex).join()) === '-1,0,-1', 'tabIndex của radiogroup sai');
  await page.focus(NUT('dark'));
  await page.keyboard.press('ArrowRight');
  let s = await trangThai(page);
  ky(s.chon === 'system' && await page.evaluate(() => document.activeElement?.dataset.chonGiaoDien) === 'system', `→ từ Tối: ${JSON.stringify(s)}`);
  await page.keyboard.press('ArrowRight');
  ky((await trangThai(page)).chon === 'light', '→ ở nút cuối không vòng về Sáng');
  await page.keyboard.press('ArrowLeft');
  ky((await trangThai(page)).chon === 'system', '← không lùi về Hệ thống');
  ky(await page.getAttribute(NUT('system'), 'aria-label') === 'Hệ thống', 'aria-label của nút Hệ thống');
  await ctx.close();
}

// 6. localStorage bị chặn (ném lỗi): trang vẫn hiện (Tối), bộ chọn vẫn đổi được cho lần xem này
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  await ctx.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('chặn', 'SecurityError'); } });
  });
  const page = await trang(ctx);
  await page.goto(base + '/');
  ky((await trangThai(page)).theme === 'dark', 'localStorage bị chặn: không về Tối');
  await page.click(NUT('light'));
  const s = await trangThai(page);
  ky(s.theme === 'light' && s.checked.join() === 'light', `localStorage bị chặn: không đổi được giao diện ${JSON.stringify(s)}`);
  await ctx.close();
}

// 7. Không JavaScript: bộ chọn ẩn, trang ở Tối (mặc định trong HTML)
{
  const ctx = await browser.newContext({ colorScheme: 'light', javaScriptEnabled: false });
  const page = await trang(ctx, false);
  await page.goto(base + '/');
  ky(await page.isHidden('#giao-dien'), 'không JavaScript: bộ chọn vẫn hiện (bấm không làm gì)');
  ky(await page.evaluate(() => getComputedStyle(document.body).backgroundColor) === NEN_RGB.dark, 'không JavaScript: nền không phải Tối');
  await ctx.close();
}

// 8. Màn hình hẹp: không cuộn ngang, bộ chọn và hai nút đầu trang nằm trong khung nhìn
for (const rong of [320, 390, 1280]) {
  const ctx = await browser.newContext({ viewport: { width: rong, height: 700 } });
  const page = await trang(ctx);
  await page.goto(base + '/');
  ky(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `rộng ${rong}px: trang cuộn ngang`);
  for (const sel of ['#giao-dien', '.dau-trang__nut']) {
    const hop = await page.locator(sel).boundingBox();
    ky(hop && hop.x >= 0 && hop.x + hop.width <= rong, `rộng ${rong}px: ${sel} tràn khung nhìn ${JSON.stringify(hop)}`);
  }
  await ctx.close();
}

await browser.close();
dong();
for (const l of loi) console.error('[theme] LỖI', l);
console.log(`[theme] ${loi.length} lỗi`);
process.exit(loi.length ? 1 : 0);
