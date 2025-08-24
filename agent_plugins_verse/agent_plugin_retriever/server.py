"""
TicketRetrieverPlugin server module.

MCP Server to expose a semantic retrieval tool: search_tickets over an SSE transport.

- search_tickets(query: str, k: int = 5, filters: dict | None = None) -> list[dict]
    Runs an embedding for `query`, performs vector search against TiDB, and returns matched tickets
    (ticket_uid, score/distance, subject, snippet/body, answer).
"""

import os
import json
import traceback
from typing import List, Dict, Optional

from mcp.server.fastmcp import FastMCP

# Embedding clients
try:
    from google import genai
    from google.genai.types import EmbedContentConfig
except Exception:
    genai = None

from sentence_transformers import SentenceTransformer

# TiDB vector client + SQL access
from tidb_vector.integrations import TiDBVectorClient
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()


# ---- MCP server config ----
NAME = "Ticket Retriever Tool"
HOST = "0.0.0.0"
PORT = 9002

mcp = FastMCP(NAME, host=HOST, port=PORT)

# ---- Environment / connection config (set these env vars) ----
TIDB_CONN = os.getenv("TIDB_CONN")  # e.g. mysql+pymysql://user:pass@host:4000/yourdb
VECTOR_TABLE = os.getenv("TIDB_VECTOR_TABLE", "ticket_embeddings")
DOC_TABLE = os.getenv("TIDB_DOC_TABLE", "tickets_data_set")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "384"))  # set to the dimension you used (384/1536/etc)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # optional - required for Gemini

# ---- Clients initialization ----
# TiDB Vector client (used for query). Do not drop existing table in production.
vs_client = TiDBVectorClient(
    table_name=VECTOR_TABLE,
    connection_string=TIDB_CONN,
    vector_dimension=VECTOR_DIM,
    drop_existing_table=False,
)

# SQL engine for fetching original documents
sql_engine = create_engine(TIDB_CONN)

# Local embedder fallback (lazy init)
_local_embedder = None


def _local_embed(texts: List[str]) -> List[List[float]]:
    global _local_embedder
    if _local_embedder is None:
        # small, fast model — adjust to your preference
        _local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embs = _local_embedder.encode(texts)
    # sentence_transformers returns numpy arrays -> convert to lists
    return [e.tolist() for e in embs]


def _gemini_embed(texts: List[str], dim: int = VECTOR_DIM) -> List[List[float]]:
    """
    Generate embeddings via Gemini (google-genai).
    Requires GOOGLE_API_KEY env var set and google-genai installed.
    """
    if genai is None:
        raise RuntimeError("google-genai SDK not available (pip install google-genai)")

    client = genai.Client(api_key=GOOGLE_API_KEY)
    resp = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=dim),
    )
    return [emb.values for emb in resp.embeddings]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Wrapper that prefers Gemini if API key is present; otherwise uses local fallback.
    """
    if GOOGLE_API_KEY and genai is not None:
        try:
            return _gemini_embed(texts)
        except Exception as e:
            # If remote fails, fallback
            print("Gemini embedding failed, falling back to local model:", e)
            traceback.print_exc()
            return _local_embed(texts)
    else:
        return _local_embed(texts)


class TicketRetrieverPlugin:
    """
    MCP plugin exposing ticket retrieval functionality.
    """

    @staticmethod
    @mcp.tool()
    def search_tickets(query: str, k: int = 5, filters: Optional[Dict] = None) :
        """
        Search similar tickets in the vector store using a semantic embedding query.

        Args:
            query (str): Natural-language query string (e.g., "encryption error after update").
            k (int, optional): Number of top results to return. Defaults to 5.
            filters (dict, optional): Metadata-based filters to narrow down results server-side.


        """
        try:
            # 1) Embed the query text
            q_emb = embed_texts([query])[0]

            # 2) Query the vector store
            result = vs_client.query(q_emb, k=k, filter=filters if filters else None)

            # 3) Process each match in the result
            # out = []
            # for match in result.matches:
            #     meta = match.metadata or {}
            #     out.append({
            #         "ticket_uid": str(match.id),
            #         "score": float(getattr(match, "distance", 0.0)),
            #         "subject": meta.get("subject") or meta.get("document"),
            #         "body": meta.get("body"),
            #         "answer": meta.get("answer"),
            #         "meta": meta,
            #     })

            return result

        except Exception as exc:
            print("search_tickets error:", exc)
            traceback.print_exc()
            return [{"error": str(exc)}]

    @staticmethod
    def display_runtime_info():
        """Prints out the server’s host and port information to the console."""
        if HOST == "0.0.0.0":
            print(f"{NAME} : Server running on IP: localhost and Port: {PORT}")
            print(f"{NAME} : Server running on IP: 127.0.0.1 and Port: {PORT}")
        print(f"{NAME} : Server running on IP: {HOST} and Port: {PORT}")

    def run(self, transport: str = "sse"):
        """Starts the MCP server and displays the IP address and port."""
        self.display_runtime_info()
        mcp.run(transport=transport)


if __name__ == "__main__":
    server = TicketRetrieverPlugin()
    server.run()
