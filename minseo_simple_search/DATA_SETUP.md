# 🗄️ 데이터베이스 설정 가이드

팀원들을 위한 로컬 데이터베이스 설정 방법입니다.

## 📦 필요한 파일

다음 파일들을 다운로드하세요:
- `mysql_dump.sql` (966 KB) - MySQL 데이터 덤프
- `qdrant_storage.tar.gz` (85 MB) - Qdrant 벡터 데이터

## 🚀 설정 방법

### 1️⃣ Docker Compose 시작

```bash
cd langgraph_project
docker-compose up -d mysql qdrant
```

### 2️⃣ MySQL 데이터 복원

```bash
# MySQL 컨테이너가 완전히 시작될 때까지 대기 (약 30초)
sleep 30

# 데이터 복원
docker exec -i policy_mysql mysql -u policy_user -ppolicypass123 policy_db < mysql_dump.sql

# 확인
docker exec policy_mysql mysql -u policy_user -ppolicypass123 -e "SELECT COUNT(*) FROM policies;" policy_db
```

### 3️⃣ Qdrant 데이터 복원

```bash
# 압축 해제
tar -xzf qdrant_storage.tar.gz

# Qdrant 중지
docker-compose stop qdrant

# 볼륨에 복사
docker run --rm \
  -v langgraph_project_qdrant_data:/qdrant/storage \
  -v $(pwd)/qdrant_storage_backup:/backup \
  busybox \
  sh -c "cp -r /backup/* /qdrant/storage/"

# Qdrant 시작
docker-compose up -d qdrant

# 확인 (10944 points가 나와야 함)
curl http://localhost:6335/collections/policies
```

### 4️⃣ 백엔드 시작

```bash
# 백엔드 시작
docker-compose up -d backend

# 로그 확인
docker-compose logs -f backend

# API 테스트
curl http://localhost:8000/health
```

## ✅ 확인 사항

### MySQL
```bash
docker exec policy_mysql mysql -u policy_user -ppolicypass123 -e "SELECT COUNT(*) FROM policies;" policy_db
# 결과: 508 policies
```

### Qdrant
```bash
curl http://localhost:6335/collections/policies | jq '.result.points_count'
# 결과: 10944 points
```

### Backend
```bash
curl http://localhost:8000/health
# 결과: {"status": "healthy"}
```

## 🆘 문제 해결

### MySQL 연결 오류
```bash
# 컨테이너 재시작
docker-compose restart mysql
# 로그 확인
docker-compose logs mysql
```

### Qdrant 데이터 없음
```bash
# 볼륨 확인
docker volume inspect langgraph_project_qdrant_data
# 재복원
# (위 3️⃣ 단계 반복)
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -ano | findstr :3306
netstat -ano | findstr :6335
netstat -ano | findstr :8000
```

## 📚 추가 정보

- **환경변수**: `.env.example` 참조
- **데이터베이스 스키마**: `infra/mysql/init/001_init.sql`
- **API 문서**: http://localhost:8000/docs (FastAPI 실행 후)

## 🔗 유용한 명령어

```bash
# 전체 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 서비스 재시작
docker-compose restart

# 전체 중지
docker-compose down

# 볼륨 포함 전체 삭제 (주의!)
docker-compose down -v
```

## 💬 문의

문제가 발생하면 팀 채널에 문의하세요!

