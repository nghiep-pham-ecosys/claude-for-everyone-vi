# Capstone c2 · Trích xuất số liệu thí nghiệm từ PDF

**Loại:** Build · **Thời lượng:** khoảng 3–4 giờ · **Cần:** module 01–03 · **Chi phí:** $0 ở mock mode; dưới $0,01 mỗi lần chạy thật với `claude-haiku-5-5` trên PDF mẫu 2 trang — ước tính dưới 10.000 token vào và tối đa 2 × 1.024 token ra, cỡ $0,002 (giá kiểm 24/10/2026)

## Đề bài

Đầu vào: một báo cáo thí nghiệm dạng PDF ([`data/bao_cao_thi_nghiem.pdf`](data/bao_cao_thi_nghiem.pdf) — 2 trang, số liệu **bịa**: thử kéo nhôm 6061-T6 và chất lượng nước sông).

Đầu ra: bảng JSON, mỗi dòng là **một phép đo**, gồm: thí nghiệm, mẫu, đại lượng, giá trị, đơn vị, **trang gốc**, **câu trích dẫn**, và **đã kiểm chứng hay chưa**.

```json
{"nguon": "C1", "thi_nghiem": "LR-2026-07", "mau": "A1", "dai_luong": "yield strength",
 "gia_tri": 276, "don_vi": "MPa", "trang": 1,
 "trich_dan": "Specimen A1: yield strength 276 MPa, tensile strength 310 MPa, elongation 12.1 %.",
 "da_kiem_chung": true, "ly_do": null}
```

Yêu cầu cốt lõi: **không con số nào được vào bảng mà không truy được về một câu có thật trong PDF.**

## Vì sao làm theo 3 bước

Cách ngây thơ là gửi PDF và xin luôn JSON. Nó có hai vấn đề:

1. **Citations (trích dẫn) và structured outputs không dùng chung được** trong một request. Gửi cả hai thì API trả 400 (docs Citations); `claude_vi` cũng chặn.
2. Nếu bạn xin model tự ghi "trang 2" vào JSON, đó chỉ là lời **model tự khai**. Với citations, số trang do **API** trả về từ vị trí thật trong tài liệu.

Vì vậy pipeline tách thành 3 bước — đây chính là kỹ thuật prompt chaining ở module 02:

```text
Lượt 1  citations          PDF (citations.enabled)  ──▶  trích dẫn nguyên văn + số trang (API trả)
Lượt 2  structured outputs  danh sách trích dẫn       ──▶  JSON đúng schema, mỗi dòng trỏ về id trích dẫn
Bước 3  code                bảng + text từng trang PDF ──▶  đánh dấu dòng nào kiểm chứng được
```

Ở lượt 2, trường `nguon` là `enum` gồm các id trích dẫn (`C1`, `C2`...). Structured outputs đảm bảo model **chỉ** trỏ tới trích dẫn có thật. Bước 3 kiểm thêm hai điều mà schema không đảm bảo được: câu trích dẫn có đúng ở trang đó không, và con số trong bảng có đúng là con số trong câu đó không.

## Chạy

```bash
CLAUDE_MOCK=1 uv run python capstones/c2-trich-xuat-pdf/pipeline.py                    # lời giải
CLAUDE_MOCK=1 uv run python capstones/c2-trich-xuat-pdf/pipeline.py --cham exercises   # code của bạn
```

Ở mock mode:

- **Lượt 1** chạy "thật" trên PDF: mock đọc PDF bằng `pypdf` rồi trích mọi câu kết thúc bằng dấu chấm và có ít nhất 2 con số, kèm `page_location` đúng trang.
- **Lượt 2** mock không hiểu nội dung, nên trả về một dòng tối thiểu theo schema (`gia_tri: 0.0`). **Bước 3 sẽ đánh dấu dòng đó là chưa kiểm chứng** — đúng việc nó phải làm. Test `test_pipeline_end_to_end_voi_fixture` dùng một fixture viết tay để kiểm cả đường thành công.

## Việc của bạn

[`exercises/trich_xuat.py`](exercises/trich_xuat.py) có ba hàm cần viết; docstring mô tả chi tiết từng hàm. Phần nối các bước ([`pipeline.py`](pipeline.py)) đã cho sẵn.

| Hàm | Bước | Kỹ năng |
|---|---|---|
| `doc_trich_dan(msg)` | Lượt 1 | Đọc `citations` (`page_location`), bỏ trùng, kiểm `stop_reason` |
| `yeu_cau_cau_truc(trich_dan)` | Lượt 2 | Prompt có XML, JSON schema strict, `enum` cho id nguồn, không gửi lại PDF |
| `kiem_chung(phep_do, trich_dan, trang_pdf)` | Bước 3 | Đối chiếu với PDF gốc; bắt số bịa và trích dẫn sai trang |

```bash
CHAM=exercises uv run pytest capstones/c2-trich-xuat-pdf -q
```

## Tiêu chí hoàn thành

- [ ] 15/15 test xanh với `CHAM=exercises`.
- [ ] `pipeline.py --cham exercises` chạy được ở mock mode.
- [ ] (Khi có key) Chạy thật trên PDF mẫu: mọi phép đo trong 6 câu kết quả đều có trong bảng, và mọi dòng `da_kiem_chung: true`.
- [ ] (Mở rộng) Tự tạo một PDF khác bằng cách sửa `PAGES` trong [`data/tao_pdf_mau.py`](data/tao_pdf_mau.py), thêm một câu có số liệu gây nhiễu (ví dụ ngày tháng), xem pipeline xử lý thế nào.

## Bẫy thường gặp

- **Bật citations và `output_config.format` trong cùng một request** → 400.
- **Gửi lại PDF ở lượt 2.** Tốn token (mỗi trang PDF thường 1.500–3.000 token, cộng phần ảnh), và nếu còn bật citations thì bị 400.
- **Tin số trang do model tự viết** thay vì số trang lấy từ citation.
- **Coi `da_kiem_chung` là đúng tuyệt đối.** Bước 3 chỉ chứng minh con số **có xuất hiện** trong câu trích dẫn, không chứng minh nó được gán đúng đại lượng (ví dụ nhầm 276 là tensile strength). Muốn chặt hơn thì kiểm thêm tên đại lượng, hoặc cho người duyệt.
- **So chuỗi mà không chuẩn hoá khoảng trắng.** Text rút từ PDF có thể có xuống dòng, khoảng trắng lạ.
- **Quên `7,2` (dấu phẩy thập phân)** khi đọc tài liệu tiếng Việt.

## An toàn nội dung

Capstone khoa học của repo **không** dùng đề bài về tổng hợp hoá chất nguy hiểm, mầm bệnh hay vũ khí. Khi tự tạo PDF để mở rộng, hãy giữ chủ đề vật liệu, môi trường, đo lường.

## Nguồn (kiểm 24/10/2026)

| Chủ đề | Nguồn |
|---|---|
| Bật citations trên document; `page_location` (trang đánh số từ 1, `end_page_number` không tính); `cited_text` không tính vào output token; **citations và structured outputs không dùng chung được** | [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) |
| Block document PDF base64; đặt PDF trước text; mỗi trang thường 1.500–3.000 token text, cộng token ảnh | [PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) |
| `output_config.format`, giới hạn JSON Schema, `enum` | [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |

PDF mẫu do repo tự sinh bằng [`data/tao_pdf_mau.py`](data/tao_pdf_mau.py); xem [NOTICE.md](../../NOTICE.md).
