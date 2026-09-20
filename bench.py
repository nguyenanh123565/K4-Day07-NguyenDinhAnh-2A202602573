from __future__ import annotations

import sys
import glob
from pathlib import Path
from src.models import Document
from src.store import EmbeddingStore
from src.chunking import FixedSizeChunker

BENCHMARK_QUERIES = [
    {
        "query": "Thời hạn đổi trả tối đa cho đơn hàng mua trực tuyến là bao lâu?",
        "gold_answer": "Thường là 30 ngày kể từ ngày nhận hàng; lỗi nhà sản xuất lên đến 6 tháng đối với UNIQLO, Long Châu cho phép 30 ngày và 1 năm với máy thiết bị y tế.",
        "filter": None
    },
    {
        "query": "Trường hợp nào được miễn phí vận chuyển đổi trả?",
        "gold_answer": "Nếu lỗi từ nhà bán, nhà sản xuất, hoặc vận chuyển. Biti's nêu rõ lỗi từ cửa hàng hoặc giao sai sản phẩm được miễn phí.",
        "filter": None
    },
    {
        "query": "Sản phẩm đã qua sử dụng hoặc có tem bị rách có được đổi trả không?",
        "gold_answer": "Thường không. Yêu cầu sản phẩm còn mới, chưa qua sử dụng, nguyên vẹn, chưa giặt, đầy đủ phụ kiện/tem nhãn.",
        "filter": None
    },
    {
        "query": "Khách hàng cần gửi thông báo đổi trả trong thời gian nào nếu nhận thiếu phụ kiện hoặc hàng bị bể vỡ?",
        "gold_answer": "Với L'Oréal, khách hàng cần thông báo trong vòng 48 giờ kể từ ngày nhận hàng.",
        "filter": None
    },
    {
        "query": "Nếu khách hàng thay đổi quyết định sau khi nhận hàng, có thể yêu cầu trả hàng trên Shopee trong bao lâu không?",
        "gold_answer": "Gửi yêu cầu trong vòng 15 ngày kể từ ngày giao hàng thành công; thực phẩm tươi sống/đông lạnh là 24 giờ.",
        "filter": None
    }
]
def parse_markdown_file(file_path: Path) -> tuple[dict, str]:
    content_text = file_path.read_text(encoding="utf-8")
    frontmatter = {}
    
    if content_text.startswith("---"):
        parts = content_text.split("---", 2)
        if len(parts) >= 3:
            fm_raw = parts[1].strip()
            body = parts[2].strip()
            for line in fm_raw.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()
            return frontmatter, body
    return {}, content_text

def run_benchmark():
    # Tự động ghi toàn bộ kết quả ra file ket_qua_benchmark.txt với chuẩn UTF-8
    sys.stdout = open("ket_qua_nhom_benchmark.txt", "w", encoding="utf-8")
    
    print("=== BAT DAU CHAY BENCHMARK RAG ===")
    
    store = EmbeddingStore(collection_name="benchmark_collection")
    
    md_files = glob.glob("data/**/*.md", recursive=True)
    if not md_files:
        md_files = glob.glob("data/*.md")
        
    print(f"Tim thay {len(md_files)} file Markdown.")
    
    total_chunks = 0
    chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    
    for file_path_str in md_files:
        path = Path(file_path_str)
        frontmatter, body = parse_markdown_file(path)
        
        chunks = chunker.chunk(body)
        
        docs_to_add = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{path.stem}#{i}"
            metadata = {
                **frontmatter,
                "doc_id": path.stem,
                "title": frontmatter.get("title", path.stem)
            }
            docs_to_add.append(Document(id=doc_id, content=chunk, metadata=metadata))
            
        store.add_documents(docs_to_add)
        total_chunks += len(docs_to_add)
        print(f"-> Nap file {path.name}: {len(chunks)} chunks.")

    print(f"\nTong so chunk: {total_chunks}\n")
    
    for idx, q_item in enumerate(BENCHMARK_QUERIES, start=1):
        query = q_item["query"]
        gold = q_item["gold_answer"]
        metadata_filter = q_item["filter"]
        
        print(f"--------------------------------------------------")
        print(f"Query {idx}: {query}")
        if metadata_filter:
            print(f"Filter: {metadata_filter}")
            results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=3)
            
        print(f"Gold Answer: {gold}")
        print("Top-3 Retrieval:")
        for r_idx, r in enumerate(results, start=1):
            doc_id = r["metadata"].get("doc_id", "unknown")
            score = r.get("score", 0.0)
            snippet = r["content"][:100].replace("\n", " ")
            print(f"  [{r_idx}] Doc: {doc_id} | Score: {score:.4f} | Snippet: {snippet}...")
            
    print("\n=== HOAN TAT BENCHMARK ===")

if __name__ == "__main__":
    run_benchmark()