# FAISS Index Setup Guide for Railway

현재 FAISS 인덱스 파일이 270MB로 GitHub 용량 제한을 초과합니다.

## 로컬에서는 작동 중 ✅
- backend/data/index/faiss.index (213MB)
- backend/data/index/meta.jsonl (57MB, 36,282 문서)

## Railway 배포 옵션

### 옵션 1: 외부 스토리지 사용 (추천)

1. **Google Drive/Dropbox에 업로드:**
   ```bash
   # faiss.index와 meta.jsonl을 업로드
   ```

2. **Railway 환경변수 설정:**
   ```
   FAISS_INDEX_URL=https://your-storage-url/faiss.index
   META_JSONL_URL=https://your-storage-url/meta.jsonl
   ```

3. **첫 배포 시 자동 다운로드:**
   `download_rag_data.py` 스크립트가 자동 실행

### 옵션 2: Railway Shell에서 직접 업로드

```bash
# Railway CLI로 접속
railway shell

# 로컬에서 scp 또는 wget으로 전송
# (Railway Volume이 있다면 직접 마운트)
```

### 옵션 3: 임시로 MockRAGService 사용

현재 배포 상태:
- ⚠️ FAISS 인덱스 없음
- ✅ MockRAGService로 기본 응답
- ✅ 채팅 기능은 정상 작동

데이터 추가 후:
- ✅ 실제 NASA 논문 기반 답변
- ✅ 36,282개 문서 검색 가능

## 추천 방안

**1단계:** 일단 현재 상태로 배포 (MockRAGService)
**2단계:** Google Drive에 데이터 업로드
**3단계:** 환경변수 설정하고 재배포
**4단계:** 실제 RAG 작동 확인

---

**현재 상태:** 로컬 완벽 작동, 프로덕션은 데이터 추가 필요
