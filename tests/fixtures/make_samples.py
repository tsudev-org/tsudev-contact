# -*- coding: utf-8 -*-
"""Sinh tệp CSV mẫu TỔNG HỢP (tên giả, số giả) để kiểm thử tay và chụp giao diện.

KHÔNG dùng danh bạ thật. Chạy: python tests/fixtures/make_samples.py <thư-mục-đích>
"""
import csv
import random
import sys
from pathlib import Path

HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương']
DEM = ['Văn', 'Thị', 'Hữu', 'Minh', 'Thanh', 'Ngọc', 'Đức', 'Thu', 'Quốc', 'Hoài']
TEN = ['An', 'Bình', 'Chi', 'Dũng', 'Giang', 'Hà', 'Khánh', 'Lan', 'Long', 'Mai', 'Nam', 'Phúc', 'Quân', 'Sơn', 'Trang', 'Tú', 'Vy', 'Yến']
COQUAN = ['UBND xã Mẫu', 'Trạm Y tế xã Mẫu', 'Công an xã Mẫu', 'Trường THCS Mẫu', 'Hội Nông dân xã Mẫu']
CHUCVU = ['Chủ tịch', 'Phó Chủ tịch', 'Công chức Văn phòng', 'Trưởng trạm', 'Kế toán', '']


def build(count: int, seed: int = 7):
    rnd = random.Random(seed)
    rows = []
    for i in range(count):
        name = f'{rnd.choice(HO)} {rnd.choice(DEM)} {rnd.choice(TEN)}'
        phone = '09' + ''.join(rnd.choice('0123456789') for _ in range(8))
        rows.append([name, phone, f'nguoidung{i}@example.com' if rnd.random() < .5 else '',
                     rnd.choice(COQUAN), rnd.choice(CHUCVU), f'{rnd.randint(1, 28):02d}/{rnd.randint(1, 12):02d}/{rnd.randint(1960, 2000)}' if rnd.random() < .4 else '',
                     'Số giả để kiểm thử' if rnd.random() < .2 else ''])
    # Các ca đặc biệt
    rows[3][1] = rows[1][1]                                     # trùng số
    rows[5][1] = rows[5][1][1:]                                 # Excel làm mất số 0
    rows[7][0] = ''                                             # thiếu tên
    rows[9][1] = 'không có'                                     # số sai
    rows[11][2] = 'email-sai@'                                  # email sai
    rows[13][5] = '31/02/1990'                                  # ngày sai
    rows[15][0] = 'An\nEND:VCARD\nBEGIN:VCARD\nFN:Gia mao\nTEL:19001234'  # thử chèn vCard
    rows[17][6] = '=HYPERLINK("http://evil.example","bấm")'    # thử chèn công thức
    rows[19][1] = rows[19][1] + ' / 024.3825.1234'              # 2 số
    return rows


def main(target: str):
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    header = ['Họ và tên', 'Số điện thoại', 'Email', 'Cơ quan', 'Chức vụ', 'Ngày sinh', 'Ghi chú']
    for name, count, enc, delim in (('mau-1200-utf8.csv', 1200, 'utf-8-sig', ','),
                                    ('mau-60-cham-phay.csv', 60, 'utf-8', ';')):
        with open(out / name, 'w', encoding=enc, newline='') as f:
            w = csv.writer(f, delimiter=delim)
            w.writerow(header)
            w.writerows(build(count))
    print(f'Đã sinh mẫu tại {out}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
