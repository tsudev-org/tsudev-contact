// Kiểm tra bản build (ECOSYSTEM_IDENTITY mục 2.2 và 4): mọi trang có title đúng khuôn, og:site_name = tsudev, canonical
// không www, description 120-160 ký tự, không CSS nội tuyến (CSP), script duy nhất là /theme.js nạp chặn trong <head>
// trước stylesheet và được CSP cho phép, liên kết mở tab mới có rel đủ,
// chỉ dùng gạch ngang ngắn trong chữ hiển thị (AGENTS.md mục 7), liên kết nội bộ không gãy.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = join(dirname(fileURLToPath(import.meta.url)), '../dist');
const loi = [];
const lienKet = [];
function duyet(thuMuc) {
  for (const e of readdirSync(thuMuc, { withFileTypes: true })) {
    const p = join(thuMuc, e.name);
    if (e.isDirectory()) duyet(p);
    else if (e.isFile() && e.name.endsWith('.html')) kiemTra(p, readFileSync(p, 'utf8'));
  }
}
function kiemTra(tep, html) {
  const ten = tep.slice(dist.length);
  const title = html.match(/<title>([^<]*)<\/title>/)?.[1] ?? '';
  if (!/^(.+ - )?tsudev-contact \| tsudev$/.test(title)) loi.push(`${ten}: title sai khuôn: ${title}`);
  if (!html.includes('<meta property="og:site_name" content="tsudev">')) loi.push(`${ten}: thiếu og:site_name tsudev`);
  if (!/<link rel="canonical" href="https:\/\/contact\.tsudev\.com\//.test(html)) loi.push(`${ten}: thiếu canonical`);
  const mota = html.match(/<meta name="description" content="([^"]*)"/)?.[1] ?? '';
  const dai = [...mota.replace(/&[a-z#0-9]+;/g, 'x')].length;
  if (dai < 120 || dai > 160) loi.push(`${ten}: description ${dai} ký tự (cần 120-160)`);
  // Script: đúng một thẻ <script src="/theme.js"></script> (không defer/async/module: phải chặn để không nháy màu),
  // nằm trong <head> và trước stylesheet đầu tiên. Script nội tuyến bị CSP chặn im lặng ở production.
  const theScript = [...html.matchAll(/<script(?![^>]*type="application\/ld\+json")[^>]*>/g)].map((m) => m[0]);
  if (theScript.length !== 1 || theScript[0] !== '<script src="/theme.js">') loi.push(`${ten}: script phải đúng một <script src="/theme.js">: ${theScript.join(' ')}`);
  const viTriScript = html.indexOf('<script src="/theme.js">');
  const viTriCss = html.search(/<link[^>]*rel="stylesheet"/);
  if (viTriScript < 0 || viTriScript > html.indexOf('</head>') || (viTriCss >= 0 && viTriScript > viTriCss)) loi.push(`${ten}: theme.js phải nằm trong <head>, trước stylesheet`);
  const luaChon = [...html.matchAll(/data-chon-giao-dien="([a-z]+)"/g)].map((m) => m[1]).join(',');
  if (luaChon !== 'light,warm,dark,system') loi.push(`${ten}: menu giao diện cần đủ light,warm,dark,system: ${luaChon}`);
  if (/<style[\s>]/.test(html) || / style="/.test(html)) loi.push(`${ten}: có CSS nội tuyến (CSP chặn)`);
  for (const a of html.matchAll(/<a [^>]*target="_blank"[^>]*>/g)) {
    if (!a[0].includes('rel="noopener noreferrer"')) loi.push(`${ten}: thiếu rel noopener noreferrer: ${a[0]}`);
  }
  // Em-dash/en-dash trong phần chữ do trang này viết. Nhật ký thay đổi và giấy phép bên thứ ba sao nguyên văn
  // từ upstream (ngoại lệ đã ghi trong logs/STATE.md) nên được bỏ qua.
  if (!/^\/(nhat-ky|ban-quyen)\//.test(ten)) {
    const chu = html.replace(/<pre[\s\S]*?<\/pre>/g, '').replace(/<[^>]+>/g, ' ');
    if (/[\u2013\u2014]/.test(chu)) loi.push(`${ten}: có em-dash/en-dash trong chữ hiển thị`);
  }
  for (const m of html.matchAll(/(?:href|src)="(\/[^"#?]*)/g)) lienKet.push([ten, m[1]]);
}
duyet(dist);
// CSP của production (public/_headers -> dist/_headers): cho phép script cùng nguồn, không 'unsafe-inline'/'unsafe-eval'
const csp = readFileSync(join(dist, '_headers'), 'utf8').match(/Content-Security-Policy:\s*(.+)/)?.[1] ?? '';
const scriptSrc = csp.split(';').map((x) => x.trim()).find((x) => x.startsWith('script-src ')) ?? '';
if (!scriptSrc.split(/\s+/).includes("'self'")) loi.push(`_headers: CSP thiếu script-src 'self' (theme.js sẽ bị chặn): ${csp}`);
if (/'unsafe-(inline|eval)'/.test(csp)) loi.push(`_headers: CSP không được có 'unsafe-inline'/'unsafe-eval'`);
if (!existsSync(join(dist, 'theme.js'))) loi.push('thiếu dist/theme.js');
for (const [ten, duong] of lienKet) {
  const dich = join(dist, decodeURI(duong));
  if (!existsSync(dich) && !existsSync(join(dich, 'index.html'))) loi.push(`${ten}: liên kết nội bộ gãy: ${duong}`);
}
for (const l of loi) console.error('[check-dist] LỖI', l);
console.log(`[check-dist] ${loi.length} lỗi`);
process.exit(loi.length ? 1 : 0);
