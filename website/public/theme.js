// Chế độ màu của contact.tsudev.com, cùng khóa và giá trị với tsudev.com: localStorage "tsudev-theme" = light|warm|dark|system.
// Nạp CHẶN trong <head>, trước stylesheet (không defer/async/module): đặt data-theme trước khung hình đầu, không nháy màu.
// Tệp tĩnh cùng nguồn nên CSP chỉ cần script-src 'self' (public/_headers), không cần 'unsafe-inline' hay băm.
(function () {
  'use strict';
  var KHOA = 'tsudev-theme';
  var CHE_DO = ['light', 'warm', 'dark', 'system'];
  var MAC_DINH = 'system';   // trước khi có nút, trang đã đi theo hệ điều hành
  var NEN = { light: '#EEF4FB', warm: '#F6F1E6', dark: '#0F1B2D' };   // --bg-base của tokens.css
  var goc = document.documentElement;
  var heThong = null;
  try { heThong = window.matchMedia('(prefers-color-scheme: dark)'); } catch (e) { heThong = null; }

  function docLuaChon() {
    try {
      var v = window.localStorage.getItem(KHOA);
      return CHE_DO.indexOf(v) >= 0 ? v : MAC_DINH;
    } catch (e) {
      return MAC_DINH;   // chặn cookie, iframe sandbox: về mặc định, không làm hỏng trang
    }
  }
  function giai(chon) {
    return chon === 'system' ? (heThong && heThong.matches ? 'dark' : 'light') : chon;
  }
  function dongBoMauThanh() {
    var mau = NEN[goc.getAttribute('data-theme')] || NEN.light;
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) metas[i].setAttribute('content', mau);
  }
  function dongBoMenu() {
    var chon = goc.getAttribute('data-theme-chon');
    var muc = document.querySelectorAll('[data-chon-giao-dien]');
    for (var i = 0; i < muc.length; i++) {
      muc[i].setAttribute('aria-checked', muc[i].getAttribute('data-chon-giao-dien') === chon ? 'true' : 'false');
    }
  }
  function apDung(chon) {
    goc.setAttribute('data-theme', giai(chon));
    goc.setAttribute('data-theme-chon', chon);   // có thuộc tính này thì CSS bỏ phương án dự phòng không JavaScript
    dongBoMauThanh();
    dongBoMenu();
  }
  function luu(chon) {
    try { window.localStorage.setItem(KHOA, chon); } catch (e) { /* không lưu được: vẫn đổi cho lần xem này */ }
    apDung(chon);
  }

  apDung(docLuaChon());

  if (heThong) {
    var khiHeThongDoi = function () { if (goc.getAttribute('data-theme-chon') === 'system') apDung('system'); };
    if (heThong.addEventListener) heThong.addEventListener('change', khiHeThongDoi);
    else if (heThong.addListener) heThong.addListener(khiHeThongDoi);
  }
  // Đổi ở thẻ khác thì thẻ này theo
  window.addEventListener('storage', function (e) { if (e.key === KHOA) apDung(docLuaChon()); });

  function ganNut() {
    dongBoMauThanh();   // các thẻ meta theme-color nằm sau script có thể chưa được đọc lúc chạy lần đầu
    var vo = document.getElementById('giao-dien');
    if (!vo) return;
    var nut = vo.querySelector('button[aria-haspopup]');
    var menu = vo.querySelector('[role="menu"]');
    var muc = Array.prototype.slice.call(menu.querySelectorAll('[role="menuitemradio"]'));
    vo.hidden = false;   // không JavaScript thì nút không làm được gì: chỉ hiện khi script chạy
    dongBoMenu();

    function mo(viTri) {
      menu.hidden = false;
      nut.setAttribute('aria-expanded', 'true');
      var i = viTri === 'cuoi' ? muc.length - 1 : Math.max(0, muc.findIndex(function (m) { return m.getAttribute('aria-checked') === 'true'; }));
      muc[i].focus();
    }
    function dong(traFocus) {
      if (menu.hidden) return;
      menu.hidden = true;
      nut.setAttribute('aria-expanded', 'false');
      if (traFocus) nut.focus();
    }
    nut.addEventListener('click', function () { if (menu.hidden) mo(); else dong(true); });
    nut.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); mo(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); mo('cuoi'); }
    });
    muc.forEach(function (m, i) {
      m.addEventListener('click', function () { luu(m.getAttribute('data-chon-giao-dien')); dong(true); });
      m.addEventListener('keydown', function (e) {
        var den = null;
        if (e.key === 'ArrowDown') den = (i + 1) % muc.length;
        else if (e.key === 'ArrowUp') den = (i - 1 + muc.length) % muc.length;
        else if (e.key === 'Home') den = 0;
        else if (e.key === 'End') den = muc.length - 1;
        else if (e.key === 'Escape') { e.preventDefault(); dong(true); return; }
        else if (e.key === 'Tab') { dong(false); return; }
        if (den !== null) { e.preventDefault(); muc[den].focus(); }
      });
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') dong(true); });
    document.addEventListener('click', function (e) { if (!vo.contains(e.target)) dong(false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ganNut);
  else ganNut();
})();
