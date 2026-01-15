"""
Data Ingestion Script
data.json → MySQL + Qdrant 적재

Usage:
    python scripts/ingest_data.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import get_settings
from app.config.logger import get_logger
from app.db.engine import get_db, init_db
from app.db.models import Policy, Document, DocTypeEnum
from app.vector_store import get_qdrant_manager, get_embedder, chunk_text

from qdrant_client.models import PointStruct

logger = get_logger()
settings = get_settings()


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """
    JSON 파일 로드
    
    Args:
        file_path: JSON 파일 경로
    
    Returns:
        List[Dict]: 정책 데이터 리스트
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} policies from {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}", exc_info=True)
        raise


def ingest_to_mysql(policies_data: List[Dict[str, Any]]) -> List[int]:
    """
    MySQL에 정책 데이터 적재
    
    Args:
        policies_data: 정책 데이터 리스트
    
    Returns:
        List[int]: 생성된 정책 ID 리스트
    """
    policy_ids = []
    
    try:
        with get_db() as db:
            for policy_data in policies_data:
                # Check if policy already exists
                existing = db.query(Policy).filter(
                    Policy.program_id == policy_data["program_id"]
                ).first()
                
                if existing:
                    logger.info(f"Policy {policy_data['program_id']} already exists, skipping")
                    policy_ids.append(existing.id)
                    continue
                
                # Parse date
                collected_date = None
                if policy_data.get("collected_date"):
                    try:
                        collected_date = datetime.strptime(
                            policy_data["collected_date"], "%Y-%m-%d"
                        ).date()
                    except:
                        pass
                
                # Create policy
                policy = Policy(
                    program_id=policy_data["program_id"],
                    region=policy_data.get("region"),
                    category=policy_data.get("category"),
                    program_name=policy_data["program_name"],
                    program_overview=policy_data.get("program_overview"),
                    support_description=policy_data.get("support_description"),
                    support_budget=policy_data.get("support_budget"),
                    support_scale=policy_data.get("support_scale"),
                    supervising_ministry=policy_data.get("supervising_ministry"),
                    apply_target=policy_data.get("apply_target"),
                    announcement_date=policy_data.get("announcement_date"),
                    biz_process=policy_data.get("biz_process"),
                    application_method=policy_data.get("application_method"),
                    contact_agency=policy_data.get("contact_agency"),
                    contact_number=policy_data.get("contact_number"),
                    required_documents=policy_data.get("required_documents"),
                    collected_date=collected_date
                )
                
                db.add(policy)
                db.flush()  # Get policy.id
                
                # Create documents for chunking
                doc_fields = {
                    "OVERVIEW": policy_data.get("program_overview", ""),
                    "TARGET": policy_data.get("apply_target", ""),
                    "SUPPORT": policy_data.get("support_description", ""),
                    "PROCESS": policy_data.get("biz_process", ""),
                    "CONTACT": f"{policy_data.get('contact_agency', '')} {policy_data.get('application_method', '')}"
                }
                
                for doc_type, content in doc_fields.items():
                    if content and content.strip():
                        document = Document(
                            policy_id=policy.id,
                            doc_type=DocTypeEnum(doc_type),
                            content=content,
                            chunk_index=0,
                            doc_metadata={
                                "region": policy_data.get("region"),
                                "category": policy_data.get("category"),
                                "program_id": policy_data["program_id"]
                            }
                        )
                        db.add(document)
                
                policy_ids.append(policy.id)
                
                if len(policy_ids) % 10 == 0:
                    logger.info(f"Processed {len(policy_ids)} policies")
            
            db.commit()
            logger.info(f"Successfully ingested {len(policy_ids)} policies to MySQL")
            
    except Exception as e:
        logger.error(f"Error ingesting to MySQL: {e}", exc_info=True)
        raise
    
    return policy_ids


def ingest_to_qdrant() -> int:
    """
    Qdrant에 문서 임베딩 적재
    
    Returns:
        int: 적재된 청크 개수
    """
    try:
        # Initialize Qdrant
        qdrant_manager = get_qdrant_manager()
        embedder = get_embedder()
        
        # Create collection (if not exists)
        qdrant_manager.create_collection(
            vector_size=embedder.dimension,
            force_recreate=False
        )
        
        # Get all documents from MySQL
        with get_db() as db:
            documents = db.query(Document).all()
            logger.info(f"Found {len(documents)} documents to embed")
            
            if not documents:
                logger.warning("No documents found in MySQL")
                return 0
            
            # Prepare chunks
            all_chunks = []
            for doc in documents:
                # Chunk document content
                chunks = chunk_text(
                    text=doc.content,
                    metadata={
                        "policy_id": doc.policy_id,
                        "doc_type": doc.doc_type.value,
                        **(doc.doc_metadata if doc.doc_metadata else {})
                    }
                )
                
                all_chunks.extend([
                    {
                        "content": chunk["content"],
                        "metadata": {
                            **chunk["metadata"],
                            "document_id": doc.id,
                            "chunk_index": chunk["chunk_index"]
                        }
                    }
                    for chunk in chunks
                ])
            
            logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
            
            # Embed chunks in batches
            batch_size = 32
            total_points = 0
            
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                
                # Extract texts
                texts = [chunk["content"] for chunk in batch]
                
                # Generate embeddings
                embeddings = embedder.embed_batch(
                    texts=texts,
                    batch_size=batch_size,
                    show_progress=True
                )
                
                # Create points
                points = []
                for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                    point_id = int(uuid.uuid4().int >> 64)  # Generate unique ID
                    
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": chunk["content"],
                            **chunk["metadata"]
                        }
                    )
                    points.append(point)
                
                # Upsert to Qdrant
                qdrant_manager.upsert_points(points)
                total_points += len(points)
                
                logger.info(f"Uploaded batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size}")
            
            logger.info(f"Successfully ingested {total_points} chunks to Qdrant")
            return total_points
            
    except Exception as e:
        logger.error(f"Error ingesting to Qdrant: {e}", exc_info=True)
        raise


def main():
    """Main ingestion workflow"""
    try:
        logger.info("=" * 60)
        logger.info("Starting data ingestion")
        logger.info("=" * 60)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Load data
        data_path = Path(__file__).parent.parent / "data.json"
        if not data_path.exists():
            # Try parent directory
            data_path = Path(__file__).parent.parent.parent / "data.json"
        
        if not data_path.exists():
            raise FileNotFoundError(f"data.json not found at {data_path}")
        
        logger.info(f"Loading data from {data_path}")
        policies_data = load_json_data(str(data_path))
        
        # Ingest to MySQL
        logger.info("Ingesting to MySQL...")
        policy_ids = ingest_to_mysql(policies_data)
        logger.info(f"MySQL ingestion complete: {len(policy_ids)} policies")
        
        # Ingest to Qdrant
        logger.info("Ingesting to Qdrant...")
        chunk_count = ingest_to_qdrant()
        logger.info(f"Qdrant ingestion complete: {chunk_count} chunks")
        
        logger.info("=" * 60)
        logger.info("Data ingestion completed successfully!")
        logger.info(f"Total policies: {len(policy_ids)}")
        logger.info(f"Total chunks: {chunk_count}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Data ingestion failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

