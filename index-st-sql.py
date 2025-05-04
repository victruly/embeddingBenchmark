from datasets import load_dataset
import requests
import json
from supabase import create_client, Client
import time
import os
import pymssql

# sentence-transformers/all-MiniLM-L6-v2
# BAAI/bge-base-zh-v1.5
# BAAI/bge-small-zh-v1.5
# BAAI/bge-large-zh-v1.5
# BAAI/bge-m3
# jinaai/jina-embeddings-v2-base-zh
# thenlper/gte-small-zh
# thenlper/gte-base-zh
# thenlper/gte-large-zh
# maidalun1020/bce-embedding-base_v1
# nomic-ai/nomic-embed-text-v1.5
# intfloat/multilingual-e5-small
# intfloat/multilingual-e5-base
# intfloat/multilingual-e5-large
# aspire/acge_text_embedding
# DMetaSoul/Dmeta-embedding-zh
# infgrad/stella-mrl-large-zh-v3.5-1792d
# infgrad/stella-large-zh-v2
# infgrad/stella-base-zh-v2

# 模型名稱
model_name = 'jinaai/jina-embeddings-v3'
print(model_name)

# 載入資料集
dataset = load_dataset("MediaTek-Research/TCEval-v2", "drcd")

# SQL Server 連線設定
DB_SERVER = 'phqairobt01.twn.psc'  # 替換為您的 SQL Server 名稱或 IP
DB_DATABASE = 'TranslateUAT'  # 替換為您的資料庫名稱
DB_USER = 'airuser'  # 替換為您的使用者名稱
DB_PASSWORD = 'translate#MIS#UAT'  # 替換為您的密碼
table_name = 'your_table_name'  # 替換為您的資料表名稱


#insert paragraphs
def insert_paragraphs(content, embedding, model):
    try:
        SQL_STATEMENT = """INSERT INTO paragraphs (content,embedding,model)
            VALUES (%s,%s,%s)"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(
            SQL_STATEMENT,
            (
                content,
                embedding,
                model
            )
        )
        inserted_id = cur.fetchone()[0]  # 獲取 IDENTITY 欄位值
        conn.commit()
        cur.close()
        conn.close()
        return inserted_id
    except Exception as e:
        print(f"Error insert insert_paragraphs into database: {e}")
        # subject = f"AIR主機:{socket.gethostname()}, roomid={roomid} insert_voicetranslog 發生錯誤 !!"
        # body = f"{repr(e)}, roomid={roomid}, username={username}, filename={filename}, content={content}, spent_time={spent_time}, srcLang={srcLang}, zh={zh}, en={en}, jp={jp}, model_name={model_name}, trans_params={trans_params}, hostname={hostname}, original_text={original_text}, avg_probs={avg_probs}, ffmpeg_spent_time={ffmpeg_spent_time}, whisper_spent_time={whisper_spent_time}, translate_spent_time={translate_spent_time}, duration={duration}, volume={volume}, wordlens={wordlens}, detectlang={detectlang}"
        # MeetingRooms.send_mail(subject=subject, body=body, to_email=Config.MIS_ADMIN, from_email=Config.MAIL_FROM)


#insert questions
def insert_questions(dataset_id, content, embedding,model, paragraph_id):
    try:
        SQL_STATEMENT = """INSERT INTO paragraphs (dataset_id, content, embedding,model, paragraph_id)
            VALUES (%s,%s,%s)"""
        conn = pymssql.connect(
            server=DB_SERVER,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cur = conn.cursor()
        cur.execute(
            SQL_STATEMENT,
            (
                dataset_id,
                content,
                embedding,
                model,
                paragraph_id
            )
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error insert insert_questions into database: {e}")
        # subject = f"AIR主機:{socket.gethostname()}, roomid={roomid} insert_voicetranslog 發生錯誤 !!"
        # body = f"{repr(e)}, roomid={roomid}, username={username}, filename={filename}, content={content}, spent_time={spent_time}, srcLang={srcLang}, zh={zh}, en={en}, jp={jp}, model_name={model_name}, trans_params={trans_params}, hostname={hostname}, original_text={original_text}, avg_probs={avg_probs}, ffmpeg_spent_time={ffmpeg_spent_time}, whisper_spent_time={whisper_spent_time}, translate_spent_time={translate_spent_time}, duration={duration}, volume={volume}, wordlens={wordlens}, detectlang={detectlang}"
        # MeetingRooms.send_mail(subject=subject, body=body, to_email=Config.MIS_ADMIN, from_email=Config.MAIL_FROM)




from sentence_transformers import SentenceTransformer

model = SentenceTransformer(model_name, trust_remote_code=True)

current_paragraph = ''
current_paragraph_id = 0


# 將資料寫入 SQL Server
# for item in dataset['train']:
for i in range(0, 3493):
    print(i)
    data = dataset["test"][i]
    if current_paragraph != data["paragraph"]:
        embedding = model.encode(data["paragraph"], normalize_embeddings=True).tolist()
        paragraph_id = insert_paragraphs(data["paragraph"], embedding, model_name)
        current_paragraph = data["paragraph"]
        current_paragraph_id = paragraph_id
    q_embedding = model.encode(data["question"], normalize_embeddings=True).tolist()
    insert_questions(i, data["question"], q_embedding, model_name, current_paragraph_id)

print("資料已成功寫入 SQL Server!")



# 建立 SQL Server 連線
# connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
# conn = pyodbc.connect(connection_string)
# cursor = conn.cursor()

# 確保資料表存在 (如果不存在則建立)
# create_table_query = f"""
# IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
# CREATE TABLE paragraphs (
#     id INT IDENTITY(1,1) PRIMARY KEY,
#     context NVARCHAR(MAX),
#     embedding NVARCHAR(MAX),
#     model NVARCHAR(MAX)
# )
# CREATE TABLE questions (
#     id INT IDENTITY(1,1) PRIMARY KEY,
#     dataset_id int,
#     content NVARCHAR(MAX),
#     embedding NVARCHAR(MAX),
#     model NVARCHAR(MAX),
#     paragraph_id int
# )
# """
# cursor.execute(create_table_query)
# conn.commit()