#!/usr/bin/env python3
"""AI DevOps SRE - Knowledge Base Ingest Script (Bulletproof Edition)"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Embeddings ─────────────────────────────────────────────────────
EMBED_SOURCE = None
for mod_name, import_path in [
    ("langchain_huggingface", "from langchain_huggingface import HuggingFaceEmbeddings"),
    ("langchain_community.embeddings", "from langchain_community.embeddings import HuggingFaceEmbeddings"),
    ("langchain.embeddings", "from langchain.embeddings import HuggingFaceEmbeddings"),
]:
    try:
        exec(import_path)
        EMBED_SOURCE = mod_name
        break
    except ImportError:
        continue

if EMBED_SOURCE is None:
    print("[FATAL] Cannot import HuggingFaceEmbeddings.")
    print("Run: pip install langchain-huggingface")
    sys.exit(1)

# Re-import for actual use
if EMBED_SOURCE == "langchain_huggingface":
    from langchain_huggingface import HuggingFaceEmbeddings
elif EMBED_SOURCE == "langchain_community.embeddings":
    from langchain_community.embeddings import HuggingFaceEmbeddings
else:
    from langchain.embeddings import HuggingFaceEmbeddings

# ── Text Splitter ────────────────────────────────────────────────
SPLITTER_SOURCE = None
for mod_name, import_path in [
    ("langchain_text_splitters", "from langchain_text_splitters import RecursiveCharacterTextSplitter"),
    ("langchain_core.text_splitter", "from langchain_core.text_splitter import RecursiveCharacterTextSplitter"),
    ("langchain.text_splitter", "from langchain.text_splitter import RecursiveCharacterTextSplitter"),
]:
    try:
        exec(import_path)
        SPLITTER_SOURCE = mod_name
        break
    except ImportError:
        continue

if SPLITTER_SOURCE is None:
    print("[FATAL] Cannot import RecursiveCharacterTextSplitter.")
    print("Run: pip install langchain-text-splitters")
    sys.exit(1)

if SPLITTER_SOURCE == "langchain_text_splitters":
    from langchain_text_splitters import RecursiveCharacterTextSplitter
elif SPLITTER_SOURCE == "langchain_core.text_splitter":
    from langchain_core.text_splitter import RecursiveCharacterTextSplitter
else:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

# ── Vector Store ───────────────────────────────────────────────────
VECTOR_SOURCE = None
for mod_name, import_path in [
    ("langchain_chroma", "from langchain_chroma import Chroma"),
    ("langchain_community.vectorstores", "from langchain_community.vectorstores import Chroma"),
    ("langchain.vectorstores", "from langchain.vectorstores import Chroma"),
]:
    try:
        exec(import_path)
        VECTOR_SOURCE = mod_name
        break
    except ImportError:
        continue

if VECTOR_SOURCE is None:
    print("[FATAL] Cannot import Chroma.")
    print("Run: pip install langchain-chroma  OR  pip install chromadb")
    sys.exit(1)

if VECTOR_SOURCE == "langchain_chroma":
    from langchain_chroma import Chroma
elif VECTOR_SOURCE == "langchain_community.vectorstores":
    from langchain_community.vectorstores import Chroma
else:
    from langchain.vectorstores import Chroma

# ── Document Loader ──────────────────────────────────────────────
LOADER_SOURCE = None
for mod_name, import_path in [
    ("langchain_community.document_loaders", "from langchain_community.document_loaders import TextLoader"),
    ("langchain.document_loaders", "from langchain.document_loaders import TextLoader"),
]:
    try:
        exec(import_path)
        LOADER_SOURCE = mod_name
        break
    except ImportError:
        continue

if LOADER_SOURCE == "langchain_community.document_loaders":
    from langchain_community.document_loaders import TextLoader
    LOADER_OK = True
elif LOADER_SOURCE == "langchain.document_loaders":
    from langchain.document_loaders import TextLoader
    LOADER_OK = True
else:
    LOADER_OK = False

# ── Document Schema ──────────────────────────────────────────────
DOC_SOURCE = None
for mod_name, import_path in [
    ("langchain_core.documents", "from langchain_core.documents import Document"),
    ("langchain.schema", "from langchain.schema import Document"),
]:
    try:
        exec(import_path)
        DOC_SOURCE = mod_name
        break
    except ImportError:
        continue

if DOC_SOURCE == "langchain_core.documents":
    from langchain_core.documents import Document
elif DOC_SOURCE == "langchain.schema":
    from langchain.schema import Document
else:
    # Fallback: define our own minimal Document class
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

# ── Config ────────────────────────────────────────────────────────
DEFAULTS = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "persist_dir": "./vectorstore",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "docs_dir": "./docs",
}


def load_documents(docs_dir: str) -> List:
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"[ERROR] Directory not found: {docs_path.absolute()}")
        docs_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {docs_path.absolute()}")
        print("Add .txt, .md, .py, .json, .yaml, .log files there, then re-run.")
        sys.exit(1)

    documents = []
    for ext in ["*.txt", "*.md", "*.py", "*.json", "*.yaml", "*.yml", "*.log"]:
        for fp in docs_path.rglob(ext):
            try:
                if LOADER_OK:
                    loader = TextLoader(str(fp), encoding="utf-8")
                    docs = loader.load()
                else:
                    with open(fp, "r", encoding="utf-8") as f:
                        text = f.read()
                    docs = [Document(page_content=text, metadata={"source": str(fp.relative_to(docs_path))})]
                for d in docs:
                    d.metadata["source"] = str(fp.relative_to(docs_path))
                    d.metadata["file_type"] = fp.suffix
                documents.extend(docs)
                print(f"  Loaded: {fp.relative_to(docs_path)}")
            except Exception as e:
                print(f"  Failed: {fp} - {e}")

    if not documents:
        print(f"\n[WARN] No documents found in: {docs_path.absolute()}")
        sys.exit(1)

    print(f"\nTotal documents loaded: {len(documents)}")
    return documents


def split_documents(documents: List, chunk_size: int, chunk_overlap: int) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def ingest(
    docs_dir: str = DEFAULTS["docs_dir"],
    persist_dir: str = DEFAULTS["persist_dir"],
    embedding_model: str = DEFAULTS["embedding_model"],
    chunk_size: int = DEFAULTS["chunk_size"],
    chunk_overlap: int = DEFAULTS["chunk_overlap"],
    clear_existing: bool = False,
):
    print("=" * 60)
    print("AI DevOps SRE - Knowledge Base Ingestion")
    print("=" * 60)
    print(f"Embedding:  {EMBED_SOURCE}")
    print(f"Splitter:   {SPLITTER_SOURCE}")
    print(f"Vector:     {VECTOR_SOURCE}")
    print(f"Loader:     {LOADER_SOURCE or 'built-in'}")
    print(f"Document:   {DOC_SOURCE or 'built-in'}")
    print("-" * 60)
    print(f"Docs:       {Path(docs_dir).absolute()}")
    print(f"Vector DB:  {Path(persist_dir).absolute()}")
    print(f"Model:      {embedding_model}")
    print("=" * 60)

    print("\nLoading documents...")
    documents = load_documents(docs_dir)

    print("\nSplitting documents...")
    chunks = split_documents(documents, chunk_size, chunk_overlap)

    print("\nInitializing embeddings (this may download the model)...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    print("\nBuilding vector store...")
    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    if clear_existing and any(persist_path.iterdir()):
        print("Clearing existing vector store...")
        shutil.rmtree(persist_path)
        persist_path.mkdir(parents=True, exist_ok=True)

    has_existing = (persist_path / "chroma.sqlite3").exists() or list(persist_path.glob("*.bin"))

    if has_existing:
        print("Found existing vector store. Adding new documents...")
        vectorstore = Chroma(
            persist_directory=str(persist_path),
            embedding_function=embeddings,
        )
        vectorstore.add_documents(chunks)
    else:
        print("Creating new vector store...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(persist_path),
        )

    if hasattr(vectorstore, "persist"):
        vectorstore.persist()

    print(f"\nSUCCESS! Knowledge base updated with {len(chunks)} chunks.")
    print(f"Saved to: {persist_path.absolute()}")
    print("\nRestart your FastAPI app to load the new knowledge base.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", default=DEFAULTS["docs_dir"])
    parser.add_argument("--persist-dir", default=DEFAULTS["persist_dir"])
    parser.add_argument("--embedding-model", default=DEFAULTS["embedding_model"])
    parser.add_argument("--chunk-size", type=int, default=DEFAULTS["chunk_size"])
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULTS["chunk_overlap"])
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    ingest(
        docs_dir=args.docs_dir,
        persist_dir=args.persist_dir,
        embedding_model=args.embedding_model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        clear_existing=args.clear,
    )


if __name__ == "__main__":
    main()