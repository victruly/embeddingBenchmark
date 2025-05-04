from datasets import load_dataset
import requests
import json
from supabase import create_client, Client
import time
import os

model_name = "text-embedding-3-large"

dataset = load_dataset("MediaTek-Research/TCEval-v2", "drcd")

# supabase_url = 'https://xxx.supabase.co'
# supabase_api_key = ''
supabase_url = 'https://rvtnmsbntstvuzivqiej.supabase.co'
supabase_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2dG5tc2JudHN0dnV6aXZxaWVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYwNzc4MDksImV4cCI6MjA2MTY1MzgwOX0.p0N5RrC0nUFOvdhsqMb4HOzsCY2AX63GqDF9SN0XmUc'


supabase: Client = create_client(supabase_url, supabase_api_key)

supabase.table('questions').delete().eq('model', model_name).execute()
supabase.table('paragraphs').delete().eq('model', model_name).execute()

# -----

# openai_api_key = os.environ['OPENAI_API_KEY']
openai_api_key = "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"


def get_embeddings(input, model):
  payload = { "input": input, "model": model }
  headers = { "Authorization": f'Bearer {openai_api_key}', "Content-Type": "application/json" }
  response = requests.post('https://api.openai.com/v1/embeddings', headers = headers, data = json.dumps(payload) )
  obj = json.loads(response.text)
  if response.status_code == 200 :
    return obj["data"][0]["embedding"]
  else:
    time.sleep(3)
    print("embedding error..... retrying")
    # retry
    return get_embeddings(input, model)

current_paragraph = ''
current_paragraph_id = 0

for i in range(0, 3493):
    print(i)
    data = dataset["test"][i]
    if current_paragraph != data["paragraph"]:
      embedding = get_embeddings( data["paragraph"], model_name )
      response = supabase.table('paragraphs').upsert({"content": data["paragraph"], "embedding": embedding, "model": model_name }).execute()
      current_paragraph = data["paragraph"]
      current_paragraph_id = response.data[0]["id"]

    q_embedding = get_embeddings( data["question"], model_name )
    supabase.table('questions').upsert({"dataset_id": i, "content": data["question"], "embedding": q_embedding, "model": model_name, "paragraph_id": current_paragraph_id }).execute()
