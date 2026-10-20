"""Working example: Milvus Lite 3.2 with two dense fields, a BM25 function field and RRF hybrid search.

Verified 2026-10-20 with pymilvus 3.0.2 / milvus-lite 3.2.2 on Python 3.12, macOS arm64.
Run: uv run --python 3.12 --with "pymilvus[milvus-lite]>=3" python references/milvus_lite_hybrid.py /tmp/spike.db
Output seen: bm25 [("2512", -2.019)]; bm25 sv [("2222", -1.492)]; hybrid top 2512, 5.3 ms.
Gotcha: Milvus Lite returns BM25 scores as negative numbers (lower is better), unlike Milvus server.
"""
import sys, time, random
from pymilvus import MilvusClient, DataType, Function, FunctionType, AnnSearchRequest, RRFRanker
db = sys.argv[1]
c = MilvusClient(db)
if c.has_collection("t"): c.drop_collection("t")
s = c.create_schema(auto_id=False)
s.add_field("code", DataType.VARCHAR, max_length=4, is_primary=True)
s.add_field("text", DataType.VARCHAR, max_length=8000, enable_analyzer=True, analyzer_params={"type": "standard"})
s.add_field("vec_a", DataType.FLOAT_VECTOR, dim=768)
s.add_field("vec_b", DataType.FLOAT_VECTOR, dim=1024)
s.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR)
s.add_function(Function(name="bm25", function_type=FunctionType.BM25, input_field_names=["text"], output_field_names=["sparse"]))
ip = c.prepare_index_params()
ip.add_index("vec_a", index_type="FLAT", metric_type="COSINE")
ip.add_index("vec_b", index_type="FLAT", metric_type="COSINE")
ip.add_index("sparse", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")
c.create_collection("t", schema=s, index_params=ip)
docs = [("2512","mjukvaruutvecklare systemutvecklare software developer backend"),("2421","organisationsutvecklare management consultant"),("2222","sjuksköterska nurse"),("3511","drifttekniker it operations technician")]
rows=[{"code":k,"text":t,"vec_a":[random.random() for _ in range(768)],"vec_b":[random.random() for _ in range(1024)]} for k,t in docs]
c.insert("t", rows); c.load_collection("t")
q="backend developer"
r = c.search("t", data=[q], anns_field="sparse", limit=3, output_fields=["code"])
print("bm25:", [(h["entity"]["code"], round(h["distance"],3)) for h in r[0]])
r = c.search("t", data=["sjuksköterska"], anns_field="sparse", limit=3, output_fields=["code"])
print("bm25 sv:", [(h["entity"]["code"], round(h["distance"],3)) for h in r[0]])
reqs=[AnnSearchRequest(data=[rows[0]["vec_a"]], anns_field="vec_a", param={}, limit=3),
      AnnSearchRequest(data=[rows[0]["vec_b"]], anns_field="vec_b", param={}, limit=3),
      AnnSearchRequest(data=[q], anns_field="sparse", param={}, limit=3)]
t=time.perf_counter(); r=c.hybrid_search("t", reqs, ranker=RRFRanker(60), limit=3, output_fields=["code"]); dt=(time.perf_counter()-t)*1000
print("hybrid:", [(h["entity"]["code"], round(h["distance"],4)) for h in r[0]], f"{dt:.1f} ms")
