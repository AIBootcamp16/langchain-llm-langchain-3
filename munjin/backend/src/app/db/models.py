"""
SQLAlchemy ORM Models
MySQL 스키마와 매핑되는 모델들
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, Date, DateTime, 
    ForeignKey, Index, Enum, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


# ============================================================
# Enums
# ============================================================

class DocTypeEnum(str, enum.Enum):
    """문서 타입"""
    OVERVIEW = "overview"
    TARGET = "target"
    SUPPORT = "support"
    PROCESS = "process"
    CONTACT = "contact"
    OTHER = "other"


class WorkflowTypeEnum(str, enum.Enum):
    """워크플로우 타입"""
    SEARCH = "SEARCH"
    QA = "QA"
    ELIGIBILITY = "ELIGIBILITY"


class RoleEnum(str, enum.Enum):
    """채팅 역할"""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class ResultEnum(str, enum.Enum):
    """판정 결과"""
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class SourceTypeEnum(str, enum.Enum):
    """웹 소스 타입"""
    DUCKDUCKGO = "duckduckgo"
    TAVILY = "tavily"
    OTHER = "other"


# ============================================================
# Model 1: Policy (정책 메타 정보)
# ============================================================

class Policy(Base):
    """정책 메타 정보 모델"""
    
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="정책 고유 ID")
    program_id = Column(Integer, unique=True, nullable=False, comment="프로그램 ID")
    region = Column(String(50), comment="지역")
    category = Column(String(50), comment="카테고리")
    program_name = Column(String(255), nullable=False, comment="정책명")
    program_overview = Column(Text, comment="정책 개요")
    support_description = Column(Text, comment="지원 내용")
    support_budget = Column(BigInteger, comment="지원 예산 (원)")
    support_scale = Column(String(255), comment="지원 규모")
    supervising_ministry = Column(String(255), comment="주관 부처")
    apply_target = Column(Text, comment="신청 대상")
    announcement_date = Column(String(100), comment="공고일")
    biz_process = Column(Text, comment="사업 프로세스")
    application_method = Column(JSON, comment="신청 방법 (배열 또는 문자열)")  # Text에서 JSON으로 변경
    contact_agency = Column(JSON, comment="문의처 (배열)")  # String에서 JSON으로 변경
    contact_number = Column(JSON, comment="연락처 (배열)")
    required_documents = Column(JSON, comment="필요 서류 (배열)")
    collected_date = Column(Date, comment="수집일")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일")
    
    # Relationships
    documents = relationship("Document", back_populates="policy", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="policy")
    checklist_results = relationship("ChecklistResult", back_populates="policy")
    web_sources = relationship("WebSource", back_populates="policy")
    
    # Indexes
    __table_args__ = (
        Index("idx_region", "region"),
        Index("idx_category", "category"),
        Index("idx_program_name", "program_name"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.program_name})>"


# ============================================================
# Model 2: Document (정책 문서)
# ============================================================

class Document(Base):
    """정책 문서 모델 (청킹용)"""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="문서 고유 ID")
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, comment="정책 ID")
    doc_type = Column(Enum(DocTypeEnum), nullable=False, comment="문서 타입")
    content = Column(Text, nullable=False, comment="문서 내용")
    chunk_index = Column(Integer, default=0, comment="청크 인덱스")
    doc_metadata = Column(JSON, comment="메타데이터")  # 'metadata'는 SQLAlchemy 예약어
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # Relationships
    policy = relationship("Policy", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index("idx_policy_id", "policy_id"),
        Index("idx_doc_type", "doc_type"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, policy_id={self.policy_id}, type={self.doc_type})>"


# ============================================================
# Model 3: Session (멀티턴 세션)
# ============================================================

class Session(Base):
    """멀티턴 세션 모델"""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, comment="세션 ID (UUID)")
    user_id = Column(String(255), comment="사용자 ID")
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), comment="정책 ID")
    workflow_type = Column(Enum(WorkflowTypeEnum), nullable=False, comment="워크플로우 타입")
    state = Column(JSON, comment="세션 상태")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일")
    
    # Relationships
    policy = relationship("Policy", back_populates="sessions")
    slots = relationship("Slot", back_populates="session", cascade="all, delete-orphan")
    checklist_results = relationship("ChecklistResult", back_populates="session", cascade="all, delete-orphan")
    web_sources = relationship("WebSource", back_populates="session")
    chat_history = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_policy_id", "policy_id"),
        Index("idx_workflow_type", "workflow_type"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, workflow={self.workflow_type})>"


# ============================================================
# Model 4: Slot (사용자 입력 슬롯)
# ============================================================

class Slot(Base):
    """사용자 입력 슬롯 모델"""
    
    __tablename__ = "slots"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="슬롯 고유 ID")
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, comment="세션 ID")
    slot_name = Column(String(100), nullable=False, comment="슬롯 이름")
    slot_value = Column(Text, comment="슬롯 값")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # Relationships
    session = relationship("Session", back_populates="slots")
    
    # Indexes
    __table_args__ = (
        Index("idx_session_id", "session_id"),
        Index("idx_slot_name", "slot_name"),
        UniqueConstraint("session_id", "slot_name", name="unique_session_slot"),
    )
    
    def __repr__(self) -> str:
        return f"<Slot(id={self.id}, name={self.slot_name})>"


# ============================================================
# Model 5: ChecklistResult (자격 확인 결과)
# ============================================================

class ChecklistResult(Base):
    """자격 확인 결과 모델"""
    
    __tablename__ = "checklist_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="결과 고유 ID")
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, comment="세션 ID")
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, comment="정책 ID")
    condition_name = Column(String(255), comment="조건명")
    condition_value = Column(Text, comment="조건 값")
    user_value = Column(Text, comment="사용자 값")
    result = Column(Enum(ResultEnum), nullable=False, comment="판정 결과")
    reason = Column(Text, comment="판정 사유")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # Relationships
    session = relationship("Session", back_populates="checklist_results")
    policy = relationship("Policy", back_populates="checklist_results")
    
    # Indexes
    __table_args__ = (
        Index("idx_session_id", "session_id"),
        Index("idx_policy_id", "policy_id"),
        Index("idx_result", "result"),
    )
    
    def __repr__(self) -> str:
        return f"<ChecklistResult(id={self.id}, result={self.result})>"


# ============================================================
# Model 6: WebSource (웹검색 근거)
# ============================================================

class WebSource(Base):
    """웹검색 근거 모델"""
    
    __tablename__ = "web_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="소스 고유 ID")
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="SET NULL"), comment="세션 ID")
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), comment="정책 ID")
    url = Column(String(512), comment="URL")
    title = Column(String(512), comment="제목")
    snippet = Column(Text, comment="스니펫")
    content = Column(Text, comment="전체 내용")
    fetched_date = Column(Date, comment="조회일")
    source_type = Column(Enum(SourceTypeEnum), nullable=False, comment="소스 타입")
    source_metadata = Column(JSON, comment="메타데이터")  # 'metadata'는 SQLAlchemy 예약어
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # Relationships
    session = relationship("Session", back_populates="web_sources")
    policy = relationship("Policy", back_populates="web_sources")
    
    # Indexes
    __table_args__ = (
        Index("idx_session_id", "session_id"),
        Index("idx_policy_id", "policy_id"),
        Index("idx_source_type", "source_type"),
    )
    
    def __repr__(self) -> str:
        return f"<WebSource(id={self.id}, url={self.url})>"


# ============================================================
# Model 7: ChatHistory (채팅 이력)
# ============================================================

class ChatHistory(Base):
    """채팅 이력 모델"""
    
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="채팅 고유 ID")
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, comment="세션 ID")
    role = Column(Enum(RoleEnum), nullable=False, comment="역할")
    content = Column(Text, nullable=False, comment="메시지 내용")
    chat_metadata = Column("metadata", JSON, comment="메타데이터")  # 'metadata'는 SQLAlchemy 예약어이므로 chat_metadata로 매핑
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # Relationships
    session = relationship("Session", back_populates="chat_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_session_id", "session_id"),
        Index("idx_role", "role"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, role={self.role})>"

