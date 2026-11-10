// Kiểm tra nút đổi giao diện trong Chromium thật, với CSP của production (phiếu logs/handover/20261110-02):
// 4 lựa chọn giải đúng, giữ sau khi tải lại, data-theme có ngay từ khung hình đầu (không nháy màu), theme-color theo
// chế độ, localStorage bị chặn không làm hỏng trang, bàn phím (Mũi tên, Esc) và ARIA đúng, không lỗi CSP.
// Chạy sau `npm run build`: `npm run check:theme`.
import { chromium } from 'playwright';
import { moMayChu } from './may-chu-tinh.mjs';

const { base, dong } = await moMayChu();
const browser = await chromium.launch();
const loi = [];
const ky = (dk, mo) => { if (!dk) loi.push(mo); };
const NEN = { light: '#EEF4FB', warm: '#F6F1E6', dark: '#0F1B2D' };

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
}));

// 1. "Theo hệ thống" (mặc định khi chưa lưu) theo hệ điều hành, và đổi ngay khi hệ điều hành đổi
for (const scheme of ['light', 'dark']) {
  const ctx = await browser.newContext({ colorScheme: scheme });
  const page = await trang(ctx);
  await page.goto(base + '/');
  const s = await trangThai(page);
  ky(s.theme === scheme && s.chon === 'system', `mặc định với hệ điều hành ${scheme}: ${JSON.stringify(s)}`);
  ky(s.mau.every((m) => m === NEN[scheme]), `theme-color ${scheme}: ${s.mau}`);
  await page.emulateMedia({ colorScheme: scheme === 'dark' ? 'light' : 'dark' });
  const doi = await page.waitForFunction((cu) => document.documentElement.dataset.theme !== cu, scheme, { timeout: 3000 }).then(() => true, () => false);
  ky(doi, `"Theo hệ thống" không đổi khi hệ điều hành đổi (${scheme})`);
  await ctx.close();
}

// 2. Bấm từng lựa chọn: đổi ngay, lưu đúng khóa, giữ sau khi tải lại; data-theme có trước khi body được vẽ
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  // Ghi data-theme tại thời điểm <body> bắt đầu được đọc: nếu chậm hơn lúc này thì sẽ có khung hình sai màu
  await ctx.addInitScript(() => {
    new MutationObserver((ds, ob) => {
      if (document.body) { window.__themeKhiCoBody = document.documentElement.dataset.theme; ob.disconnect(); }
    }).observe(document, { childList: true, subtree: true });   // chạy trước khi có <html>: theo dõi cả document
  });
  const page = await trang(ctx);
  await page.goto(base + '/huong-dan/');
  for (const [chon, mongDoi] of [['dark', 'dark'], ['warm', 'warm'], ['light', 'light'], ['system', 'light'], ['dark', 'dark']]) {
    await page.click('#giao-dien button[aria-haspopup]');
    ky(await page.getAttribute('#giao-dien button[aria-haspopup]', 'aria-expanded') === 'true', `${chon}: aria-expanded không thành true`);
    await page.click(`[data-chon-giao-dien="${chon}"]`);
    let s = await trangThai(page);
    ky(s.theme === mongDoi && s.chon === chon && s.luu === chon, `bấm ${chon}: ${JSON.stringify(s)}`);
    ky(await page.isHidden('#giao-dien-menu'), `${chon}: menu không đóng sau khi chọn`);
    await page.reload();
    s = await trangThai(page);
    ky(s.theme === mongDoi && s.chon === chon, `tải lại sau ${chon}: ${JSON.stringify(s)}`);
    ky(await page.evaluate(() => window.__themeKhiCoBody) === mongDoi, `${chon}: data-theme chưa có khi <body> bắt đầu (nháy màu)`);
    ky(s.mau.every((m) => m === NEN[mongDoi]), `theme-color sau ${chon}: ${s.mau}`);
    await page.click('#giao-dien button[aria-haspopup]');
    ky(await page.getAttribute(`[data-chon-giao-dien="${chon}"]`, 'aria-checked') === 'true', `${chon}: aria-checked không đúng`);
    await page.keyboard.press('Escape');
  }
  // Nền trang đổi thật theo token (không còn màu cắm cứng của chế độ Sáng)
  ky((await trangThai(page)).nen === 'rgb(15, 27, 45)', `nền chế độ Tối: ${(await trangThai(page)).nen}`);
  await ctx.close();
}

// 3. Bàn phím: Mũi tên xuống mở menu và focus mục đang chọn, Mũi tên di chuyển, Enter chọn, Esc đóng và trả focus
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  const page = await trang(ctx);
  await page.goto(base + '/');
  await page.focus('#giao-dien button[aria-haspopup]');
  await page.keyboard.press('ArrowDown');
  ky(await page.evaluate(() => document.activeElement?.dataset.chonGiaoDien) === 'system', 'Mũi tên xuống không focus mục đang chọn (system)');
  await page.keyboard.press('ArrowDown');   // vòng lại mục đầu
  ky(await page.evaluate(() => document.activeElement?.dataset.chonGiaoDien) === 'light', 'Mũi tên xuống ở mục cuối không vòng về đầu');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  ky((await trangThai(page)).theme === 'dark', 'Enter trên "Tối" không đổi sang Tối');
  ky(await page.evaluate(() => document.activeElement?.getAttribute('aria-haspopup')) === 'menu', 'focus không về nút sau khi chọn');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Escape');
  ky(await page.isHidden('#giao-dien-menu'), 'Esc không đóng menu');
  ky(await page.getAttribute('#giao-dien button[aria-haspopup]', 'aria-expanded') === 'false', 'aria-expanded không về false');
  ky(await page.evaluate(() => document.activeElement?.getAttribute('aria-haspopup')) === 'menu', 'Esc không trả focus về nút');
  await page.click('#giao-dien button[aria-haspopup]');
  await page.click('h1');
  ky(await page.isHidden('#giao-dien-menu'), 'bấm ra ngoài không đóng menu');
  await ctx.close();
}

// 4. localStorage bị chặn (ném lỗi): trang vẫn hiện theo hệ thống, nút vẫn đổi được cho lần xem này
{
  const ctx = await browser.newContext({ colorScheme: 'dark' });
  await ctx.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('chặn', 'SecurityError'); } });
  });
  const page = await trang(ctx);
  await page.goto(base + '/');
  ky((await trangThai(page)).theme === 'dark', 'localStorage bị chặn: không về "Theo hệ thống"');
  await page.click('#giao-dien button[aria-haspopup]');
  await page.click('[data-chon-giao-dien="warm"]');
  ky((await trangThai(page)).theme === 'warm', 'localStorage bị chặn: không đổi được giao diện');
  await ctx.close();
}

// 5. Giá trị lạ trong localStorage: về mặc định
{
  const ctx = await browser.newContext({ colorScheme: 'light' });
  await ctx.addInitScript(() => localStorage.setItem('tsudev-theme', '"><img src=x>'));
  const page = await trang(ctx);
  await page.goto(base + '/');
  const s = await trangThai(page);
  ky(s.theme === 'light' && s.chon === 'system', `giá trị lạ: ${JSON.stringify(s)}`);
  await ctx.close();
}

// 6. Không JavaScript: nút ẩn, trang vẫn theo hệ điều hành (phương án dự phòng trong site.css)
{
  const ctx = await browser.newContext({ colorScheme: 'dark', javaScriptEnabled: false });
  const page = await trang(ctx, false);
  await page.goto(base + '/');
  ky(await page.isHidden('#giao-dien'), 'không JavaScript: nút vẫn hiện (bấm không làm gì)');
  ky(await page.evaluate(() => getComputedStyle(document.body).backgroundColor) === 'rgb(15, 27, 45)', 'không JavaScript: không theo chế độ tối của hệ điều hành');
  await ctx.close();
}

// 7. Màn hình hẹp: nút và menu nằm trọn trong khung nhìn, không cuộn ngang
for (const rong of [320, 390, 1280]) {
  const ctx = await browser.newContext({ viewport: { width: rong, height: 700 } });
  const page = await trang(ctx);
  await page.goto(base + '/');
  await page.click('#giao-dien button[aria-haspopup]');
  const hop = await page.locator('#giao-dien-menu').boundingBox();
  ky(hop && hop.x >= 0 && hop.x + hop.width <= rong, `rộng ${rong}px: menu tràn khung nhìn ${JSON.stringify(hop)}`);
  ky(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `rộng ${rong}px: trang cuộn ngang`);
  await ctx.close();
}

await browser.close();
dong();
for (const l of loi) console.error('[theme] LỖI', l);
console.log(`[theme] ${loi.length} lỗi`);
process.exit(loi.length ? 1 : 0);
