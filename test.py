# embed_and_store.py

import os
import time
import math
import json
import pandas as pd
from sqlalchemy import create_engine
from datasets import load_dataset
from google import genai
from google.genai.types import EmbedContentConfig
from google.genai import errors as genai_errors
from tidb_vector.integrations import TiDBVectorClient
from dotenv import load_dotenv
load_dotenv()
# Optional local fallback
from sentence_transformers import SentenceTransformer

# ---- CONFIGURATION ----
TIDB_CONN = os.getenv("TIDB_CONN")  # e.g., mysql+pymysql://user:pass@host:4000/db
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")   # required for Gemini embedding
DATA_LIMIT = 0.3  # fraction of dataset to use
BATCH_SIZE = 50
MAX_RETRIES = 5
BACKOFF_BASE = 2.0
CHECKPOINT_FILE = "embed_checkpoint.json"
VECTOR_DIM = 384
TABLE_NAME = "ticket_embeddings"

# Initialize clients
engine = create_engine(TIDB_CONN)
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
vs_client = TiDBVectorClient(
    table_name=TABLE_NAME,
    connection_string=TIDB_CONN,
    vector_dimension=VECTOR_DIM,
    drop_existing_table=True,
)

# SentenceTransformers fallback
local_embedder = None
def fallback_embed(text_list):
    global local_embedder
    if not local_embedder:
        print("Initializing local fallback embedder...")
        local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return [vec.tolist() for vec in local_embedder.encode(text_list)]

# Load previous checkpoint
def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        return json.load(open(CHECKPOINT_FILE))
    return {"last_idx": 0}

def save_checkpoint(idx):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_idx": idx}, f)

# Embed batch with retry logic
def embed_with_retry(texts):
    if not client:
        return fallback_embed(texts)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=VECTOR_DIM,
                )
            )
            return [e.values for e in resp.embeddings]
        except genai_errors.ClientError as e:
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "Quota" in msg:
                wait = BACKOFF_BASE ** attempt
                print(f"[WARN] Quota hit (attempt {attempt}). Backing off {wait}s...")
                time.sleep(wait)
                continue
            raise
    print("[WARN] Retries exhausted—switching to fallback...")
    return fallback_embed(texts)

# Load and preprocess dataset
ds = load_dataset("Tobi-Bueck/customer-support-tickets", split="train")
df = ds.train_test_split(test_size=DATA_LIMIT, seed=42)["test"].to_pandas()
df = df.reset_index(drop=True)
df["ticket_uid"] = df.index.astype(str)
df["text"] = df["subject"].fillna("") + "\n\n" + df["body"].fillna("") + \
             "\n\nAnswer: " + df.get("answer", "").fillna("")

print(f"Loaded {len(df)} tickets. Starting from index null.")

# Start/resume from checkpoint
ck = load_checkpoint()
start_idx = ck["last_idx"]
print(f"Resuming from index {start_idx}")

# Main batch loop
n = len(df)
for i in range(start_idx, n, BATCH_SIZE):
    j = min(i + BATCH_SIZE, n)
    batch = df.iloc[i:j]
    print(f"Embedding batch {i}-{j-1}")
    texts = batch["text"].tolist()
    embs = embed_with_retry(texts)
    vs_client.insert(
        ids=batch["ticket_uid"].tolist(),
        texts=batch["text"].tolist(),
        embeddings=embs
    )
    save_checkpoint(j)
    print(f"Stored batch {i}-{j-1} and saved checkpoint at {j}")
    time.sleep(1)

print("Embedding & storage complete!")

# Semantic search example
query = "encryption failure after software update"
q_emb = embed_with_retry([query])[0]
results = vs_client.query(q_emb, k=5)
print("Top similar tickets:", results)
