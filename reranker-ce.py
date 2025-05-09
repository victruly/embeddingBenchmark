from supabase import create_client, Client
from datetime import datetime

# model_name = "text-embedding-3-small"
model_name = "jinaai/jina-embeddings-v2-base-zh"

print(datetime.now())
print( model_name )

# supabase_url = 'https://xxx.supabase.co'
# supabase_api_key = ''
supabase_url = 'https://rvtnmsbntstvuzivqiej.supabase.co'
supabase_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2dG5tc2JudHN0dnV6aXZxaWVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYwNzc4MDksImV4cCI6MjA2MTY1MzgwOX0.p0N5RrC0nUFOvdhsqMb4HOzsCY2AX63GqDF9SN0XmUc'


supabase: Client = create_client(supabase_url, supabase_api_key)

response1 = supabase.table('questions').select("content, embedding, paragraph_id").eq("model", model_name).execute()

question_contents = [x["content"] for x in response1.data]
question_embeddings = [ eval(x["embedding"]) for x in response1.data]

gold_paragraph_ids = [x["paragraph_id"] for x in response1.data]

response2 = supabase.table('paragraphs').select("id, content, embedding").eq("model", model_name).execute()

paragraph_ids = [x["id"] for x in response2.data]

paragraph_embeddings = [ eval(x["embedding"]) for x in response2.data]
paragraph_contents = [x["content"] for x in response2.data]


print( len(question_embeddings) ) # 應該要是 3493
print( len(paragraph_embeddings) ) # 應該要是 1000

print("Dimension:")
print( len(question_embeddings[0]) ) # 這是向量維度

print("----------------")

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 參數 list_of_doc_vectors 是所有文件的 embeddings 向量
# 參數 query_vector 是查詢字串的 embedding 向量
# 參數 top_k 是回傳的比數
def get_top_k_indices(list_of_doc_vectors, query_vector, top_k):
  # 轉成 numpy arrays
  list_of_doc_vectors = np.array(list_of_doc_vectors)
  query_vector = np.array(query_vector)

  # 逐筆計算 cosine similarities
  similarities = cosine_similarity(query_vector.reshape(1, -1), list_of_doc_vectors).flatten()

  # 根據 cosine similarity 排序
  sorted_indices = np.argsort(similarities)[::-1]

  # 取出 top K 的索引編號
  top_k_indices = sorted_indices[:top_k]

  return top_k_indices

def find_index(arr, target):
  try:
      index = arr.index(target)
      return index
  except ValueError:
      return "not_found"

def calculate_average(arr):
    if len(arr) == 0:
        return 0  # 防止除以零錯誤
    return sum(arr) / len(arr)


hit_data = []
mmr_data = []

from sentence_transformers import CrossEncoder


reranker_model = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
reranker = CrossEncoder(reranker_model, max_length=512)

print(reranker_model)

search_top_k = 50

print(search_top_k)

print(datetime.now())

for idx, question_embedding in enumerate(question_embeddings):

  print(idx)

  best_indexes = get_top_k_indices(paragraph_embeddings, question_embedding, search_top_k) # 取出 top_k 的 indexes
  # ----- reranker 後取 top 5

  rerank_docs = [paragraph_contents[i] for i in best_indexes]

  pairs = [[question_contents[idx], doc] for doc in rerank_docs]


  scores = reranker.predict(pairs)


  ordered_index = np.argsort(scores)[::-1]
  rerank_indexes = ordered_index[0:5] # 取前5

  best_best_indexes = [best_indexes[i] for i in rerank_indexes]

  context_ids = [paragraph_ids[i] for i in best_best_indexes] # 找出對應的 paragraph_ids

  # -----
  hit_paragraph_id = gold_paragraph_ids[idx] # 這是黃金 paragraph_id

  position = find_index(context_ids, hit_paragraph_id)
  if position == "not_found":
    score = 0
  else:
    score = 1 / (position+1)

  mmr_data.append( score )
  hit_data.append( hit_paragraph_id in context_ids )

average_hit = sum(hit_data) / len(hit_data)

print("---------------------------")
print(average_hit)

average_mrr = calculate_average(mmr_data)

print("MRR score:")
print(average_mrr)

print(datetime.now())
