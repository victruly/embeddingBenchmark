from supabase import create_client, Client

# model_name = "<要評測的model名稱>"
model_name = "jinaai/jina-embeddings-v3"
# model_name = ""

print( model_name )
# SQL Server 連線設定
DB_SERVER = 'phqairobt01.twn.psc'  # 替換為您的 SQL Server 名稱或 IP
DB_DATABASE = 'TranslateUAT'  # 替換為您的資料庫名稱
DB_USER = 'xxx'  # 替換為您的使用者名稱
DB_PASSWORD = 'aaa'  # 替換為您的密碼
table_name = 'your_table_name'  # 替換為您的資料表名稱

def get_question_embeddings():
    try:
        SQL_STATEMENT = """SELECT id, embedding, paragraph_id FROM questions WHERE model = %s"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(SQL_STATEMENT, (model_name,))
        # rows = cur.fetchall()
        embeddings = [row[0] for row in cursor.fetchall()] 
        return embeddings
    except Exception as e:
        print(f"Error: {e}")

def get_paragraph_embeddings():
    try:
        SQL_STATEMENT = """SELECT id, embedding FROM paragraphs WHERE model = %s"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(SQL_STATEMENT, (model_name,))
        # rows = cur.fetchall()
        embeddings = [row[0] for row in cursor.fetchall()] 
        return embeddings
    except Exception as e:
        print(f"Error: {e}")

def get_paragraph_id():
    try:
        SQL_STATEMENT = """SELECT id FROM paragraphs WHERE model = %s"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(SQL_STATEMENT, (model_name,))
        # rows = cur.fetchall()
        ids = [row[0] for row in cursor.fetchall()] 
        return ids
    except Exception as e:
        print(f"Error: {e}")

def get_gold_paragraph_id():
    try:
        SQL_STATEMENT = """SELECT id FROM questions WHERE model = %s"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(SQL_STATEMENT, (model_name,))
        # rows = cur.fetchall()
        ids = [row[0] for row in cur.fetchall()] 
        return ids
    except Exception as e:
        print(f"Error: {e}")

question_embeddings = get_question_embeddings()

gold_paragraph_ids = get_gold_paragraph_id()

paragraph_ids = get_paragraph_id()

paragraph_embeddings = get_paragraph_embeddings()

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

for idx, question_embedding in enumerate(question_embeddings):

  print(idx, end=", ")

  best_indexes = get_top_k_indices(paragraph_embeddings, question_embedding, 5) # 取出 top_k 的 indexes
  context_ids = [paragraph_ids[i] for i in best_indexes] # 找出對應的 paragraph_ids
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
