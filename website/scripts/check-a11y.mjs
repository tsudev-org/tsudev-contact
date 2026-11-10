// Kiểm tra khả năng truy cập (ACCESSIBILITY.md của tsudev) bằng axe-core: mọi trang trong dist/ ở cả 2 chế độ màu
// (Sáng, Tối - chọn qua localStorage "tsudev-theme" như người dùng bấm nút);
// quy tắc WCAG 2.0/2.1/2.2 mức A và AA. Trang được phục vụ kèm CSP của production; lỗi CSP/console cũng tính là lỗi.
// Chạy sau `npm run build`: `npm run check:a11y` (CI: website.yml). Cần Chromium của Playwright:
// `npx playwright install --with-deps chromium`.
import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import { danhSachTrang, moMayChu } from './may-chu-tinh.mjs';

const { base, dong } = await moMayChu();
const browser = await chromium.launch();
const tags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
let total = 0;
const list = danhSachTrang();
const CHE_DO = ['light', 'dark'];

async function kiem(page, nhan) {
  const { violations } = await new AxeBuilder({ page }).withTags(tags).analyze();
  for (const v of violations) {
    total++;
    console.error(`[a11y] LỖI ${nhan}: ${v.id} (${v.impact}) - ${v.help}`);
    for (const n of v.nodes.slice(0, 5)) console.error(`         ${n.target.join(' ')}: ${n.failureSummary?.split('\n').slice(1).join(' ').trim()}`);
  }
}

for (const cheDo of CHE_DO) {
  const context = await browser.newContext();
  await context.addInitScript((c) => { try { localStorage.setItem('tsudev-theme', c); } catch { /* trang lỗi */ } }, cheDo);
  for (const path of list) {
    const page = await context.newPage();
    page.on('console', (m) => { if (m.type() === 'error' && !/404 \(Not Found\)/.test(m.text())) { total++; console.error(`[a11y] LỖI console ${cheDo} ${path}: ${m.text()}`); } });
    page.on('pageerror', (e) => { total++; console.error(`[a11y] LỖI script ${cheDo} ${path}: ${e.message}`); });
    await page.goto(base + path, { waitUntil: 'load' });
    const thucTe = await page.evaluate(() => document.documentElement.dataset.theme);
    if (thucTe !== cheDo) { total++; console.error(`[a11y] LỖI ${cheDo} ${path}: data-theme = ${thucTe}`); }
    await kiem(page, `${cheDo} ${path}`);
    await page.close();
  }
  await context.close();
}
await browser.close();
dong();
console.log(`[a11y] ${list.length} trang x ${CHE_DO.length} chế độ màu, ${total} lỗi`);
process.exit(total ? 1 : 0);
