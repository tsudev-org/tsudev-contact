# Thành phần bên thứ ba

tsudev-contact đóng gói các thành phần sau. Toàn văn giấy phép đi kèm bản phát hành hoặc tại liên kết.

| Thành phần | Phiên bản | Giấy phép | Dùng cho |
| --- | --- | --- | --- |
| [Qt for Python (PySide6-Essentials)](https://doc.qt.io/qtforpython-6/) | 6.12.0 | LGPL-3.0 | Giao diện. Liên kết động: thư viện Qt nằm nguyên dạng trong gói, có thể thay bằng bản build khác. Mã nguồn Qt: <https://download.qt.io/official_releases/> |
| [Inter](https://github.com/rsms/inter) | 4.1 | SIL Open Font License 1.1 (`assets/fonts/Inter-LICENSE.txt`) | Font giao diện theo token thiết kế |
| [Lucide](https://lucide.dev) | - | ISC | Icon nét mảnh (`src/ui/icons.py`) |
| [Python](https://www.python.org) | 3.11 | PSF License | Trình thông dịch đi kèm bản `.exe` |

Không thành phần nào kết nối Internet. Danh sách đầy đủ, kèm phiên bản và mã băm, nằm trong tệp SBOM
(`*.cdx.json`) đính kèm mỗi bản phát hành.

## Giấy phép Lucide (ISC)

```
ISC License

Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT).
All other copyright (c) for Lucide are held by Lucide Contributors 2022.

Permission to use, copy, modify, and/or distribute this software for any purpose with or without
fee is hereby granted, provided that the above copyright notice and this permission notice appear
in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
```
