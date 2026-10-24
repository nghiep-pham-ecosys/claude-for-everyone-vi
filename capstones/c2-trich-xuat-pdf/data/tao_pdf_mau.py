"""Sinh data/bao_cao_thi_nghiem.pdf — báo cáo thí nghiệm GIẢ LẬP, tự viết, dùng cho capstone c2.

Không cần thư viện ngoài: ghi trực tiếp cấu trúc PDF tối thiểu, font Helvetica có sẵn.
Nội dung tiếng Anh vì font chuẩn của PDF (WinAnsi) không có dấu tiếng Việt.
Số liệu bịa, chỉ để luyện trích xuất. Chủ đề: vật liệu (kéo nhôm) và môi trường (chất lượng nước).

Chạy lại:  uv run python capstones/c2-trich-xuat-pdf/data/tao_pdf_mau.py
"""
from pathlib import Path

PAGES = [
    [
        ("Lab Report LR-2026-07: Tensile Test of Aluminium 6061-T6", 15),
        ("Prepared for teaching purposes. All values are synthetic.", 10),
        ("", 10),
        ("1. Method", 12),
        ("Specimens were machined to ASTM E8 subsize geometry and tested at 22 C", 10),
        ("with a crosshead speed of 2 mm/min. Three specimens were tested.", 10),
        ("", 10),
        ("2. Results", 12),
        ("Specimen A1: yield strength 276 MPa, tensile strength 310 MPa, elongation 12.1 %.", 10),
        ("Specimen A2: yield strength 281 MPa, tensile strength 314 MPa, elongation 11.4 %.", 10),
        ("Specimen A3: yield strength 269 MPa, tensile strength 305 MPa, elongation 13.0 %.", 10),
        ("", 10),
        ("Specimen A2 showed a small surface scratch before testing.", 10),
    ],
    [
        ("Lab Report LR-2026-08: River Water Quality, Station W3", 15),
        ("Prepared for teaching purposes. All values are synthetic.", 10),
        ("", 10),
        ("1. Sampling", 12),
        ("Grab samples were collected on 2026-09-14 at 0.5 m depth and analysed within 6 h.", 10),
        ("", 10),
        ("2. Results", 12),
        ("Sample W3-a: pH 7.2, dissolved oxygen 6.8 mg/L, turbidity 14 NTU.", 10),
        ("Sample W3-b: pH 6.9, dissolved oxygen 5.9 mg/L, turbidity 22 NTU.", 10),
        ("", 10),
        ("Turbidity of W3-b was measured twice; the reported value is the mean.", 10),
    ],
]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf() -> bytes:
    objects: list[bytes] = []
    n_pages = len(PAGES)
    # 1 catalog, 2 pages, 3 font, rồi mỗi trang 2 object (page, content)
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n_pages))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, lines in enumerate(PAGES):
        ops = ["BT"]
        y = 790
        for text, size in lines:
            ops.append(f"/F1 {size} Tf 1 0 0 1 56 {y} Tm ({_escape(text)}) Tj")
            y -= size + 8
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * i} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


if __name__ == "__main__":
    path = Path(__file__).with_name("bao_cao_thi_nghiem.pdf")
    path.write_bytes(build_pdf())
    print(f"Đã ghi {path} ({path.stat().st_size} byte, {len(PAGES)} trang)")
