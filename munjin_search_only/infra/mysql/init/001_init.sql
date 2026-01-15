-- Policy Q&A Agent Database Schema
-- Initialized: 2026-01-12

-- Set character set and time zone
SET NAMES utf8mb4;
SET time_zone = '+09:00';

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS policy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE policy_db;

-- ============================================================
-- Table 1: policies (정책 메타 정보)
-- ============================================================
CREATE TABLE IF NOT EXISTS policies (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '정책 고유 ID',
    program_id INT UNIQUE NOT NULL COMMENT '프로그램 ID (data.json의 program_id)',
    region VARCHAR(50) COMMENT '지역',
    category VARCHAR(50) COMMENT '카테고리',
    program_name VARCHAR(255) NOT NULL COMMENT '정책명',
    program_overview TEXT COMMENT '정책 개요',
    support_description TEXT COMMENT '지원 내용',
    support_budget BIGINT COMMENT '지원 예산 (원)',
    support_scale VARCHAR(255) COMMENT '지원 규모',
    supervising_ministry VARCHAR(255) COMMENT '주관 부처',
    apply_target TEXT COMMENT '신청 대상',
    announcement_date VARCHAR(100) COMMENT '공고일',
    biz_process TEXT COMMENT '사업 프로세스',
    application_method JSON COMMENT '신청 방법 (배열 또는 문자열)',
    contact_agency JSON COMMENT '문의처 (배열)',
    contact_number JSON COMMENT '연락처 (배열)',
    required_documents JSON COMMENT '필요 서류 (배열)',
    collected_date DATE COMMENT '수집일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    INDEX idx_region (region),
    INDEX idx_category (category),
    INDEX idx_program_name (program_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정책 메타 정보';

-- ============================================================
-- Table 2: documents (정책 상세 문서 - 청킹용)
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '문서 고유 ID',
    policy_id INT NOT NULL COMMENT '정책 ID',
    doc_type ENUM('OVERVIEW', 'TARGET', 'SUPPORT', 'PROCESS', 'CONTACT', 'OTHER') NOT NULL COMMENT '문서 타입',
    content TEXT NOT NULL COMMENT '문서 내용',
    chunk_index INT DEFAULT 0 COMMENT '청크 인덱스',
    doc_metadata JSON COMMENT '메타데이터 (JSON)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    INDEX idx_policy_id (policy_id),
    INDEX idx_doc_type (doc_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정책 문서 (청킹용)';

-- ============================================================
-- Table 3: sessions (멀티턴 세션 관리)
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY COMMENT '세션 ID (UUID)',
    user_id VARCHAR(255) COMMENT '사용자 ID (선택)',
    policy_id INT COMMENT '정책 ID',
    workflow_type ENUM('search', 'qa', 'eligibility') NOT NULL COMMENT '워크플로우 타입',
    state JSON COMMENT '세션 상태 (JSON)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_policy_id (policy_id),
    INDEX idx_workflow_type (workflow_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='멀티턴 세션 관리';

-- ============================================================
-- Table 4: slots (사용자 입력 정보 저장)
-- ============================================================
CREATE TABLE IF NOT EXISTS slots (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '슬롯 고유 ID',
    session_id VARCHAR(36) NOT NULL COMMENT '세션 ID',
    slot_name VARCHAR(100) NOT NULL COMMENT '슬롯 이름 (예: age, region, business_type)',
    slot_value TEXT COMMENT '슬롯 값',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_slot_name (slot_name),
    UNIQUE KEY unique_session_slot (session_id, slot_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 입력 슬롯';

-- ============================================================
-- Table 5: checklist_results (자격 확인 결과)
-- ============================================================
CREATE TABLE IF NOT EXISTS checklist_results (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '결과 고유 ID',
    session_id VARCHAR(36) NOT NULL COMMENT '세션 ID',
    policy_id INT NOT NULL COMMENT '정책 ID',
    condition_name VARCHAR(255) COMMENT '조건명',
    condition_value TEXT COMMENT '조건 값',
    user_value TEXT COMMENT '사용자 값',
    result ENUM('PASS', 'FAIL', 'UNKNOWN') NOT NULL COMMENT '판정 결과',
    reason TEXT COMMENT '판정 사유',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_policy_id (policy_id),
    INDEX idx_result (result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='자격 확인 결과';

-- ============================================================
-- Table 6: web_sources (웹검색 근거 저장)
-- ============================================================
CREATE TABLE IF NOT EXISTS web_sources (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '소스 고유 ID',
    session_id VARCHAR(36) COMMENT '세션 ID',
    policy_id INT COMMENT '정책 ID',
    url VARCHAR(512) COMMENT 'URL',
    title VARCHAR(512) COMMENT '제목',
    snippet TEXT COMMENT '스니펫',
    content TEXT COMMENT '전체 내용 (선택)',
    fetched_date DATE COMMENT '조회일',
    source_type ENUM('duckduckgo', 'tavily', 'other') NOT NULL COMMENT '소스 타입',
    metadata JSON COMMENT '메타데이터',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_policy_id (policy_id),
    INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='웹검색 근거';

-- ============================================================
-- Table 7: chat_history (대화 이력 저장)
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '채팅 고유 ID',
    session_id VARCHAR(36) NOT NULL COMMENT '세션 ID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '역할',
    content TEXT NOT NULL COMMENT '메시지 내용',
    metadata JSON COMMENT '메타데이터 (evidence, tokens 등)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='채팅 이력';

-- ============================================================
-- Sample data (for testing - optional)
-- ============================================================
-- INSERT INTO policies (program_id, region, category, program_name, program_overview, apply_target)
-- VALUES (999, '서울', '테스트', '테스트 정책', '테스트용 정책입니다.', '테스트 사용자');

-- ============================================================
-- Show tables
-- ============================================================
SHOW TABLES;

-- Success message
SELECT 'Database schema initialized successfully!' AS status;

