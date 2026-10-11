from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String)
    total_records = Column(Integer, default=0)
    
    documents = relationship("Document", back_populates="dataset")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(String, index=True)  # ID from the CSV
    text = Column(Text, nullable=False)
    normalized_text = Column(Text)
    scheme = Column(String, index=True)
    intent = Column(String, index=True)
    awareness_gap = Column(String)
    gap_type = Column(String, index=True)
    state = Column(String, index=True)
    district = Column(String, index=True)
    source = Column(String)
    source_type = Column(String)
    language = Column(String)
    source_url = Column(String)
    is_synthetic = Column(String)
    confidence = Column(String)
    notes = Column(Text)
    split = Column(String, index=True)
    
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    dataset = relationship("Dataset", back_populates="documents")
    
    collected_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Tracking model versions that produced these results (null for initial human-labeled data)
    intent_model_version = Column(String, nullable=True)
    gap_model_version = Column(String, nullable=True)
    embedding_model_version = Column(String, nullable=True)
