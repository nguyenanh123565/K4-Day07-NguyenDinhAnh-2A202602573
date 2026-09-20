# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, bảo hành và quy định người bán / người mua trên các nền tảng thương mại điện tử (K4-L3B).

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề chính sách thương mại điện tử nhằm xây dựng hệ thống hỏi đáp (FAQ/RAG) hỗ trợ khách hàng và người bán tra cứu nhanh các quy định đổi trả, thời hạn bảo hành. Dữ liệu có sự phân hóa rõ rệt giữa đối tượng người mua (buyer) và người bán (seller), rất phù hợp để áp dụng và đánh giá hiệu quả của kỹ thuật lọc Metadata Filter trong truy xuất thông tin.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách bảo hành CellphoneS | https://cellphones.com.vn/chinh-sach-bao-hanh | 2026-09-20 / not-stated | 3718 | `doc_id: cps-baohanh-01`, `audience: buyer`, `category: warranty_policy`, `language: vi` |
| 2 | Bảo hành Điện Máy Xanh | https://dmx.vn/docs/warranty | 2026-09-20 / 2024 | 331 | `doc_id: dmx_both`, `audience: both` |
| 3 | Đổi trả FPT Shop | https://fpt.vn/docs/return | 2026-09-20 / not-stated | 311 | `doc_id: fpt_buyer`, `audience: buyer` |
| 4 | Chính sách người mua Shopee | https://shopee.vn/docs/buyer | 2026-09-20 / 1.0 | 323 | `doc_id: sp_buyer`, `audience: buyer` |
| 5 | Quy định người bán Shopee | https://shopee.vn/docs/seller | 2026-09-20 / 1.0 | 319 | `doc_id: sp_seller`, `audience: seller` |
| 6 | Đổi trả Tiki | https://tiki.vn/docs/return | 2026-09-20 / not-stated | 310 | `doc_id: tk_buyer`, `audience: buyer` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | `str` | `buyer`, `seller`, `both` | Bắt buộc với biến thể L3B: Giúp lọc chính xác điều khoản theo đối tượng áp dụng (người mua vs người bán), tránh mô hình trả lời nhầm quyền lợi/nghĩa vụ của đối tượng khác. |
| `source_url` | `str` | `https://shopee.vn/docs/buyer` | Định danh nguồn trích dẫn gốc, phục vụ việc kiểm chứng và trích dẫn câu trả lời chuẩn (gold answer). |
| `retrieved_at` | `str` | `2026-09-20` | Lưu thời điểm thu thập dữ liệu phục vụ quản trị dữ liệu và theo dõi độ tươi mới của chính sách. |
| `document_version` | `str` | `1.0`, `2024`, `not-stated` | Xác định phiên bản hoặc năm áp dụng chính sách, tránh xung đột giữa chính sách cũ và mới. |
| `category` | `str` | `warranty_policy`, `policy` | Phân loại loại hình điều khoản (bảo hành, đổi trả, giải quyết tranh chấp) để thu hẹp không gian tìm kiếm vector. |
| `language` | `str` | `vi` | Định danh ngôn ngữ của tài liệu phục vụ cho mô hình embedding đa ngôn ngữ hoặc lọc ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
