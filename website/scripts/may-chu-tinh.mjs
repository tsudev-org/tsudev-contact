// Máy chủ tĩnh tối thiểu cho dist/ (chỉ 127.0.0.1, chặn vượt thư mục), gửi ĐÚNG các header của production
// (dist/_headers, khối "/*") để kiểm tra trong trình duyệt gặp cùng CSP như contact.tsudev.com.
import { createServer } from 'node:http';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, extname, join, normalize, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const dist = join(dirname(fileURLToPath(import.meta.url)), '../dist');
const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.ico': 'image/x-icon', '.webp': 'image/webp', '.woff2': 'font/woff2', '.json': 'application/json',
  '.xml': 'application/xml', '.txt': 'text/plain', '.webmanifest': 'application/manifest+json',
};

/** Header chung của mọi đường dẫn (khối "/*" trong _headers). Bỏ upgrade-insecure-requests: máy chủ thử chạy http. */
function headerChung() {
  const out = {};
  let trongKhoi = false;
  for (const dong of readFileSync(join(dist, '_headers'), 'utf8').split('\n')) {
    if (!dong.trim()) continue;
    if (!/^\s/.test(dong)) { trongKhoi = dong.trim() === '/*'; continue; }
    if (!trongKhoi) continue;
    const i = dong.indexOf(':');
    const ten = dong.slice(0, i).trim();
    if (ten === 'Strict-Transport-Security') continue;
    out[ten] = dong.slice(i + 1).trim().replace(/;\s*upgrade-insecure-requests/, '');
  }
  if (!out['Content-Security-Policy']) throw new Error('_headers không có Content-Security-Policy');
  return out;
}

export function danhSachTrang(dir = dist) {
  const out = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...danhSachTrang(p));
    else if (e.isFile() && e.name.endsWith('.html')) out.push('/' + relative(dist, p).split(sep).join('/').replace(/(^|\/)index\.html$/, '$1'));
  }
  return out.sort();
}

export async function moMayChu() {
  const chung = headerChung();
  const server = createServer((req, res) => {
    let path = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    if (path.endsWith('/')) path += 'index.html';
    const file = normalize(join(dist, path));
    // Đọc thẳng rồi bắt lỗi (không kiểm tồn tại trước: tránh TOCTOU); chặn vượt ra ngoài dist/
    let body = null;
    if (file.startsWith(dist + sep)) {
      try { body = readFileSync(file); } catch { body = null; }   // không có, hoặc là thư mục (EISDIR)
    }
    if (body === null) {
      res.writeHead(404, { ...chung, 'content-type': MIME['.html'] });
      res.end(readFileSync(join(dist, '404.html')));
      return;
    }
    res.writeHead(200, { ...chung, 'content-type': MIME[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  return { base: `http://127.0.0.1:${server.address().port}`, dong: () => server.close() };
}
