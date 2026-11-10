// Giao diện của contact.tsudev.com, cùng hợp đồng với tsudev.com (phiếu logs/handover/20261110-05 mục 3):
// localStorage "tsudev-theme" = light|dark|system; giá trị cũ "warm" đọc thành "light"; không có/không đọc được -> "dark".
// Nạp CHẶN trong <head>, sau <meta name="theme-color"> và trước stylesheet (không defer/async/module): đặt data-theme
// và màu thanh địa chỉ trước khung hình đầu, không nháy màu. Tệp tĩnh cùng nguồn nên CSP chỉ cần script-src 'self'.
(function () {
  'use strict';
  var KHOA = 'tsudev-theme';
  var LUA_CHON = ['light', 'dark', 'system'];
  var MAC_DINH = 'dark';
  var NEN = { light: '#fafafa', dark: '#0a0a0a' };   // --bg-base của src/styles/palette.css
  var goc = document.documentElement;
  var heThong = null;
  try { heThong = window.matchMedia('(prefers-color-scheme: dark)'); } catch (e) { heThong = null; }
  var trongPhien = null;   // localStorage hỏng (chặn cookie, iframe sandbox): vẫn đổi được cho lần xem này

  function docLuaChon() {
    if (trongPhien) return trongPhien;
    try {
      var v = window.localStorage.getItem(KHOA);
      if (v === 'warm') return 'light';   // chế độ Ấm đã bỏ: người từng chọn Ấm muốn nền sáng
      return LUA_CHON.indexOf(v) >= 0 ? v : MAC_DINH;
    } catch (e) {
      return MAC_DINH;
    }
  }
  function giai(chon) {
    return chon === 'system' ? (heThong && heThong.matches ? 'dark' : 'light') : chon;
  }
  function dongBoMauThanh() {
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) metas[i].setAttribute('content', NEN[goc.getAttribute('data-theme')] || NEN.dark);
  }
  function dongBoNut() {
    var chon = goc.getAttribute('data-theme-chon');
    var nut = document.querySelectorAll('[data-chon-giao-dien]');
    for (var i = 0; i < nut.length; i++) {
      var dang = nut[i].getAttribute('data-chon-giao-dien') === chon;
      nut[i].setAttribute('aria-checked', dang ? 'true' : 'false');
      nut[i].tabIndex = dang ? 0 : -1;   // radiogroup: chỉ nút đang chọn nằm trong thứ tự Tab
    }
  }
  function apDung(chon) {
    goc.setAttribute('data-theme', giai(chon));
    goc.setAttribute('data-theme-chon', chon);
    dongBoMauThanh();
    dongBoNut();
  }
  function chon(gt) {
    trongPhien = null;
    try { window.localStorage.setItem(KHOA, gt); } catch (e) { trongPhien = gt; }
    apDung(gt);
  }

  apDung(docLuaChon());

  if (heThong) {
    var khiHeThongDoi = function () { if (goc.getAttribute('data-theme-chon') === 'system') apDung('system'); };
    if (heThong.addEventListener) heThong.addEventListener('change', khiHeThongDoi);
    else if (heThong.addListener) heThong.addListener(khiHeThongDoi);
  }
  window.addEventListener('storage', function (e) { if (e.key === KHOA) { trongPhien = null; apDung(docLuaChon()); } });

  function ganNut() {
    dongBoMauThanh();
    var nhom = document.getElementById('giao-dien');
    if (!nhom) return;
    var nut = Array.prototype.slice.call(nhom.querySelectorAll('[data-chon-giao-dien]'));
    nhom.hidden = false;   // không JavaScript thì bộ chọn không làm được gì: chỉ hiện khi script chạy
    dongBoNut();
    nut.forEach(function (n, i) {
      n.addEventListener('click', function () { chon(n.getAttribute('data-chon-giao-dien')); });
      n.addEventListener('keydown', function (e) {
        // radiogroup: mũi tên chọn luôn nút kế bên (vòng quanh), như tsudev.com
        var buoc = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
        if (!buoc) return;
        e.preventDefault();
        var den = nut[(i + buoc + nut.length) % nut.length];
        chon(den.getAttribute('data-chon-giao-dien'));
        den.focus();
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ganNut);
  else ganNut();
})();
