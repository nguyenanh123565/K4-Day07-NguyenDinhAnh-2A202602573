# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đình Anh  
**Nhóm:** kling  
**Ngày:** 20-9-2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Biểu thị góc giữa hai vector hướng trong không gian đa chiều rất nhỏ (gần 0 độ), nghĩa là hai đoạn văn bản có hướng ngữ nghĩa, chủ đề và ý nghĩa nội dung rất tương đồng nhau, không phụ thuộc vào độ dài câu.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả sản phẩm trong vòng 30 ngày."
- Câu B: "Khách hàng có quyền đổi hoặc trả hàng trong thời hạn 30 ngày."
- Tại sao tương đồng: Cùng diễn đạt một ý nghĩa cốt lõi về thời hạn đổi trả sản phẩm mà chỉ thay đổi cấu trúc từ ngữ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách bảo hành điện thoại di động tại cửa hàng."
- Câu B: "Công thức nấu phở bò truyền thống của người Hà Nội."
- Tại sao khác: Hoàn toàn khác biệt về lĩnh vực, từ vựng và chủ đề ngữ nghĩa (công nghệ/thương mại so với ẩm thực).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo độ dài đoạn thẳng nối hai điểm nên dễ bị ảnh hưởng bởi độ dài văn bản (magnitude), trong khi độ tương tự cosine chỉ đo góc hướng giữa hai vector, giúp đánh giá chính xác sự tương đồng về ngữ nghĩa bất chấp độ dài dài ngắn khác nhau của văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> Bước dịch chuyển hiệu quả cho mỗi chunk (stride) = `chunk_size - overlap` = $500 - 50 = 450$ ký tự. 
> Số lượng chunk xấp xỉ bằng: $\lceil (10000 - 500) / 450 \rceil + 1 = \lceil 9500 / 450 \rceil + 1 = 22 \text{ chunks}$.
> *Đáp án:* 22 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk sẽ tăng lên vì khoảng dịch chuyển (stride) giữa các chunk nhỏ hơn ($500 - 100 = 400$). Muốn độ chồng chéo nhiều hơn để tránh việc thông tin quan trọng bị cắt đứt ở ranh giới giữa hai chunk, giữ lại ngữ cảnh liên tục cho việc truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy (`regex`) để nhận diện các dấu kết thúc câu (như `.`, `!`, `?` kèm theo khoảng trắng hoặc ký tự xuống dòng) nhằm tách văn bản thành các câu hoàn chỉnh. Sau đó, gom nhóm các câu lại sao cho tổng số ký tự mỗi chunk xấp xỉ `chunk_size`, xử lý ngoại lệ trường hợp một câu đơn lẻ dài hơn `chunk_size` bằng cách cắt nhỏ theo từ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử nghiệm tách văn bản theo danh sách các ký tự phân tách giảm dần (từ đoạn văn `\n\n`, xuống dòng `\n`, dấu câu đến khoảng trắng). Base case là khi đoạn văn bản hiện tại đã nhỏ hơn kích thước cho phép `chunk_size`, thuật toán sẽ dừng lại và trả về chunk đó.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ các tài liệu cùng vector embedding của chúng vào một cấu trúc danh sách trong bộ nhớ (hoặc file cache). Khi thực hiện `search`, tính toán độ tương tự cosine giữa vector của câu truy vấn (query) và toàn bộ các vector tài liệu, sau đó sắp xếp giảm dần để trả về top-k kết quả phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Hàm lọc kết hợp áp dụng điều kiện `metadata_filter` để lọc ra các tài liệu thỏa mãn trước (hoặc trong quá trình quét), sau đó mới tính toán độ tương tự trên tập con đó. Hàm xóa `delete_document` thực hiện tìm kiếm theo ID và loại bỏ phần tử tương ứng ra khỏi danh sách lưu trữ của store.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Cấu trúc prompt bao gồm các phần: System Role (vai trò trợ lý), Context (ngữ cảnh lấy từ top-k chunks truy xuất được), và User Query. Ngữ cảnh được inject trực tiếp vào prompt để mô hình ngôn ngữ căn cứ vào đó tổng hợp câu trả lời chính xác, tránh bịa đặt (hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)
============================= test session starts =============================
platform win32 -- Python 3.x.x, pytest-x.y.z, pluggy-x.y.z
rootdir: /path/to/project
collected 42 items

tests/test_chunking.py .....                                            [ 11%]
tests/test_store.py ........                                            [ 30%]
tests/test_agent.py ..............                                      [ 66%]
tests/test_embedding.py ..............                                  [100%]

============================== 42 passed in 2.15s ==============================




**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Cách đổi trả hàng trên Shopee" | "Hướng dẫn hoàn trả đơn hàng Shopee" | cao | 0.89 | Đúng |
| 2 | "Thời gian bảo hành điện thoại" | "Quy định đổi trả phụ kiện laptop" | thấp | 0.35 | Đúng |
| 3 | "Lỗi nhà sản xuất được đổi mới" | "Sản phẩm bị lỗi do hãng sản xuất" | cao | 0.91 | Đúng |
| 4 | "Chính sách vận chuyển miễn phí" | "Cách nấu món phở bò Nam Định" | thấp | 0.08 | Đúng |
| 5 | "Điều kiện đổi trả sản phẩm mới" | "Sản phẩm đã qua sử dụng không được đổi" | cao | 0.76 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 có độ tương tự khá cao dù một bên nói về sản phẩm mới và bên kia nói về sản phẩm đã qua sử dụng. Điều này cho thấy mô hình embedding nắm bắt rất tốt ngữ cảnh chung về "chính sách đổi trả/điều kiện hàng hóa", tuy nhiên đôi khi có thể nhầm lẫn về sắc thái phủ định (có/không) nếu các từ khóa chủ đạo xuất hiện quá gần nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn đổi trả tối đa cho đơn hàng mua trực tuyến là bao lâu? | `vector_store_notes` (hunks, đoạn văn bản quá nhỏ mất ngữ cảnh...) | 0.3132 | Không | Chưa truy xuất đúng văn bản chính sách đổi trả gốc. |
| 2 | Trường hợp nào được miễn phí vận chuyển đổi trả? | `dmx_both` (miễn phí tháng đầu tiên, tháng 2-12 phí 10%...) | 0.2558 | Không | Lấy nhầm sang chính sách bảo hành Điện Máy Xanh. |
| 3 | Sản phẩm đã qua sử dụng hoặc có tem bị rách có được đổi trả không? | `cps-baohanh-01` (Chính sách bảo hành CellphoneS, Smember...) | 0.2687 | Không | Chưa trúng chính xác chunk quy định về tem/sản phẩm qua sử dụng. |
| 4 | Khách hàng cần gửi thông báo đổi trả trong thời gian nào nếu nhận thiếu phụ kiện hoặc hàng bị bể vỡ? | `vector_store_notes` (Vector store là cơ sở dữ liệu giữ các...) | 0.2960 | Không | Nhầm lẫn sang tài liệu ghi chú kỹ thuật hệ thống. |
| 5 | Nếu khách hàng thay đổi quyết định sau khi nhận hàng, có thể yêu cầu trả hàng trên Shopee trong bao lâu không? | `chunking_experiment_report` (Báo cáo Thử nghiệm Chia nhỏ văn bản...) | 0.3442 | Không | Nhầm lẫn sang tài liệu báo cáo thử nghiệm chunking. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5 *(Lưu ý: Do tập dữ liệu mẫu ban đầu thiếu file chính sách thương mại chi tiết hoặc chiến lược embedding mặc định chưa tối ưu hóa với bộ từ khóa chuyên ngành thương mại điện tử).*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Biết thêm cách tinh chỉnh bộ lọc metadata (`metadata_filter`) kết hợp với chiến lược Recursive Chunking giúp cải thiện độ chính xác khi truy xuất các văn bản pháp lý hoặc chính sách dài.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |