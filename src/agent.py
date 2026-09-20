from __future__ import annotations

from typing import Callable
from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Truy xuất top-k chunk liên quan từ store
        results = self.store.search(question, top_k=top_k)

        # Xử lý trường hợp store rỗng hoặc không tìm thấy kết quả
        if not results:
            return "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu để trả lời câu hỏi của bạn."

        # 2. Dựng ngữ cảnh (Context) có đánh số [1], [2], [3] kèm nguồn để đảm bảo Source Traceability
        context_parts = []
        for idx, r in enumerate(results, start=1):
            if isinstance(r, dict):
                content = r.get("content", "")
                metadata = r.get("metadata", {})
            elif isinstance(r, (list, tuple)):
                content = r[0]
                metadata = r[1] if len(r) > 1 else {}
            else:
                content = str(r)
                metadata = {}
            source_title = metadata.get("title", metadata.get("doc_id", "Unknown Source"))
            context_parts.append(f"[{idx}] (Nguồn: {source_title})\n{content}")

        context_str = "\n\n".join(context_parts)

        # 3. Xây dựng prompt chống bịa đặt (Anti-hallucination) ép LLM chỉ dùng ngữ cảnh được cung cấp
        prompt = (
            f"Bạn là một trợ lý ảo hỗ trợ khách hàng dựa trên tài liệu chính sách.\n"
            f"Hãy trả lời câu hỏi dưới đây dựa CHÍNH XÁC VÀ ĐẦY ĐỦ vào các đoạn ngữ cảnh được cung cấp.\n"
            f"Nếu thông tin không có trong ngữ cảnh, hãy nói rõ là không tìm thấy. Tuyệt đối không tự bịa đặt.\n"
            f"Khi trích dẫn thông tin, hãy kèm theo số thứ tự nguồn tương ứng (ví dụ: [1]).\n\n"
            f"--- NGỮ CẢNH ---\n{context_str}\n-----------------\n\n"
            f"Câu hỏi: {question}\n"
            f"Trả lời:"
        )

        # 4. Gọi LLM để sinh câu trả lời
        return self.llm_fn(prompt)