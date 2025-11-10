import os
import pandas as pd
from sqlalchemy.orm import Session
from contextlib import contextmanager
from apps.core.db import SessionLocal, LeaderboardCache
from apps.backend.repositories.leaderboard_repo import LeaderboardRepository
import logging
from datetime import datetime


# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dockerfile.backend에서 복사한 경로
SEED_FILE_PATH = "data/seed_data.parquet" 


@contextmanager
def get_db_session():
    """DB 세션을 안전하게 관리하기 위한 컨텍스트 매니저"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database():
    """
    애플리케이션 시작 시, LeaderboardCache가 비어있으면 Parquet 파일로 DB를 초기화합니다.
    (Idempotent: 이미 데이터가 있으면 실행되지 않음)
    """
    logger.info("Checking if database seeding is required...")
    try:
        with get_db_session() as db:
            repo = LeaderboardRepository(db)

            # 1. DB에 이미 데이터가 있는지 확인 (Idempotency check)
            # get_leaderboard는 LeaderboardCache 테이블을 조회함.
            existing_data = repo.get_leaderboard(limit=1)
            if existing_data:
                logger.info("LeaderboardCache already contains data. Skipping seeding.")
                return

            # 2. 시드 파일 존재 여부 확인
            if not os.path.exists(SEED_FILE_PATH):
                logger.warning(f"Seed file not found at '{SEED_FILE_PATH}'. Skipping.")
                return

            logger.info(f"Database is empty. Seeding initial data from '{SEED_FILE_PATH}'...")
            df = pd.read_parquet(SEED_FILE_PATH)

            # 3. Parquet의 모든 점수 레코드를 DB에 삽입 (Bulk)
            logger.info(f"Preparing to seed {len(df)} score records into LeaderboardCache...")
            
            records_added = 0
            for _, row in df.iterrows():
                try:
                    # 4. leaderboard_repo.py의 upsert_entry 메서드 활용
                    # (존재하지 않는 LeaderboardRun/Result 대신 LeaderboardCache에 직접 삽입)
                    repo.upsert_entry(
                        model_name=row.model_name,
                        language=row.language,
                        subject_type=row.subject_type,
                        task_type=row.task_type,
                        score=row.score
                        # last_updated는 upsert_entry 내부에서 자동으로 설정됨
                    )
                    records_added += 1
                except Exception as row_e:
                    logger.error(f"Failed to insert row: {row}. Error: {row_e}")

            # 5. 트랜잭션 커밋
            # (upsert_entry가 매번 커밋하므로, 대량 삽입 시 repo를 수정하거나
            #  또는 repo의 commit 로직을 믿고 그대로 둠 - 현재는 후자)
            # repo.db.commit() # -> upsert_entry가 이미 commit을 수행함
            
            logger.info(f"Database seeding complete. Added {records_added} records.")

    except Exception as e:
        logger.error(f"[ERROR] Database seeding failed: {e}")
        # get_db_session()의 finally에서 db.close()가 롤백 처리 (필요시)