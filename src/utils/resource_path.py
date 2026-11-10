# -*- coding: utf-8 -*-
"""Giải đường dẫn tài nguyên cho cả môi trường dev lẫn bundle PyInstaller."""
import os
import sys

# Gốc repo khi chạy từ mã nguồn - tính theo vị trí file, KHÔNG theo thư mục hiện hành
# (bản cũ dùng os.path.abspath('.') nên chạy từ thư mục khác là mất token/icon).
_SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resourcePath(relativePath: str) -> str:
    """Trả về đường dẫn tuyệt đối tới tài nguyên đi kèm ứng dụng."""
    basePath = getattr(sys, '_MEIPASS', _SOURCE_ROOT)
    return os.path.join(basePath, relativePath)
