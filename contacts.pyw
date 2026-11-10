# -*- coding: utf-8 -*-
# tsudev-contact - một sản phẩm của tsudev (https://tsudev.com)
# Điểm khởi chạy mỏng. Toàn bộ mã nguồn nằm trong src/ (xem docs/ARCHITECTURE.md).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main.app import main

if __name__ == "__main__":
    raise SystemExit(main())
