"""
RAG (Retrieval Augmented Generation) System for DevOps Knowledge
"""
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class KnowledgeEntry:
    content: str
    source: str
    category: str
    tags: List[str]
    metadata: Dict

class DevOpsKnowledgeBase:
    def __init__(self, persist_directory: str = "./data/chroma_db",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectorstore: Optional[Chroma] = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        os.makedirs(self.persist_directory, exist_ok=True)
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info(f"Loaded knowledge base with {self.vectorstore._collection.count()} entries")
        except Exception as e:
            logger.warning(f"Creating new knowledge base: {e}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
    
    def add_knowledge(self, entries: List[KnowledgeEntry]):
        documents = []
        metadatas = []
        ids = []
        for i, entry in enumerate(entries):
            doc = Document(
                page_content=entry.content,
                metadata={
                    "source": entry.source, "category": entry.category,
                    "tags": ",".join(entry.tags), **entry.metadata
                }
            )
            documents.append(doc.page_content)
            metadatas.append(doc.metadata)
            ids.append(f"{entry.category}_{i}_{hash(entry.content) % 1000000}")
        self.vectorstore.add_texts(texts=documents, metadatas=metadatas, ids=ids)
        self.vectorstore.persist()
        logger.info(f"Added {len(entries)} knowledge entries")
    
    def query(self, query_text: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        filter_dict = {"category": category} if category else None
        results = self.vectorstore.similarity_search_with_score(
            query=query_text, k=top_k, filter=filter_dict
        )
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content, "source": doc.metadata.get("source", "unknown"),
                "category": doc.metadata.get("category", "unknown"),
                "tags": doc.metadata.get("tags", "").split(",") if doc.metadata.get("tags") else [],
                "similarity_score": round(float(score), 4),
                "metadata": {k: v for k, v in doc.metadata.items() if k not in ["source", "category", "tags"]}
            })
        return formatted_results
    
    def get_context_for_error(self, error_type: str, error_message: str, top_k: int = 3) -> str:
        results = self.query(query_text=error_message, category=error_type, top_k=top_k)
        if not results:
            return "No relevant documentation found in knowledge base."
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Reference {i}]\nSource: {result['source']}\nContent: {result['content']}\n"
            )
        return "\n\n".join(context_parts)
    
    def initialize_default_knowledge(self):
        default_entries = [
            KnowledgeEntry(
                content="""Docker Error: 'Cannot connect to Docker daemon'
Cause: Docker daemon is not running or user lacks permissions.
Fix: 
1. Start Docker service: sudo systemctl start docker
2. Add user to docker group: sudo usermod -aG docker $USER
3. Restart shell or run: newgrp docker
4. Verify: docker ps""",
                source="docker_docs", category="docker",
                tags=["daemon", "permission", "connection"], metadata={}
            ),
            KnowledgeEntry(
                content="""Docker Error: 'pull access denied'
Cause: Invalid credentials or missing repository access.
Fix:
1. Run: docker login
2. Verify registry URL is correct
3. Check repository permissions in registry settings
4. For CI/CD, ensure DOCKER_USERNAME and DOCKER_PASSWORD are set""",
                source="docker_docs", category="docker",
                tags=["registry", "authentication", "pull"], metadata={}
            ),
            KnowledgeEntry(
                content="""Kubernetes Error: 'CrashLoopBackOff'
Cause: Container repeatedly crashing.
Fix:
1. Check logs: kubectl logs <pod> --previous
2. Verify env vars: kubectl describe pod <pod>
3. Check resource limits in deployment spec
4. Review liveness/readiness probes""",
                source="kubernetes_docs", category="kubernetes",
                tags=["crashloopbackoff", "pod", "container"], metadata={}
            ),
            KnowledgeEntry(
                content="""Kubernetes Error: 'ImagePullBackOff'
Cause: Kubernetes cannot pull the container image.
Fix:
1. Verify image name and tag exist
2. Check imagePullSecrets for private registries
3. Ensure node has internet access
4. Check registry credentials""",
                source="kubernetes_docs", category="kubernetes",
                tags=["imagepullbackoff", "registry", "image"], metadata={}
            ),
            KnowledgeEntry(
                content="""Terraform Error: 'Error acquiring state lock'
Cause: Previous terraform operation didn't release the state lock.
Fix:
1. Identify lock: terraform force-unlock <LOCK_ID>
2. For S3 backend, check DynamoDB table for stale locks
3. Ensure only one process runs terraform at a time""",
                source="terraform_docs", category="terraform",
                tags=["state", "lock", "backend"], metadata={}
            ),
            KnowledgeEntry(
                content="""Terraform Error: 'Provider configuration not present'
Cause: Provider block missing or misconfigured.
Fix:
1. Add provider block
2. Run: terraform init
3. Ensure required_providers is defined in terraform block""",
                source="terraform_docs", category="terraform",
                tags=["provider", "configuration", "init"], metadata={}
            ),
            KnowledgeEntry(
                content="""YAML Error: 'mapping values are not allowed in this context'
Cause: Incorrect indentation or missing colon in YAML.
Fix:
1. Use spaces (not tabs) for indentation
2. Ensure consistent indentation (usually 2 spaces)
3. Validate YAML: yamllint or online validators""",
                source="yaml_spec", category="yaml",
                tags=["indentation", "syntax", "mapping"], metadata={}
            ),
            KnowledgeEntry(
                content="""Docker Build Error: 'failed to solve: rpc error'
Cause: BuildKit issue or invalid Dockerfile syntax.
Fix:
1. Disable BuildKit: DOCKER_BUILDKIT=0 docker build .
2. Check Dockerfile syntax
3. Clear build cache: docker builder prune""",
                source="docker_docs", category="docker",
                tags=["buildkit", "build", "rpc"], metadata={}
            ),
            KnowledgeEntry(
                content="""Kubernetes: 'OOMKilled' (Out of Memory)
Cause: Container exceeded memory limit.
Fix:
1. Increase memory limit in deployment
2. Optimize application memory usage
3. Check for memory leaks
4. Add memory requests""",
                source="kubernetes_docs", category="kubernetes",
                tags=["oomkilled", "memory", "resources"], metadata={}
            ),
            KnowledgeEntry(
                content="""Terraform: 'Resource already exists'
Cause: Resource created outside Terraform or state file mismatch.
Fix:
1. Import existing resource: terraform import <resource_type>.<name> <id>
2. Or remove resource manually and let Terraform recreate
3. Refresh state: terraform refresh""",
                source="terraform_docs", category="terraform",
                tags=["import", "state", "exists"], metadata={}
            ),
        ]
        self.add_knowledge(default_entries)
        logger.info("Initialized default DevOps knowledge base")