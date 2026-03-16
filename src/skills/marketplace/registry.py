"""
Skill Marketplace Registry - 技能市场注册表

基于SQLite的技能市场数据存储
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from .models import (
    MarketplaceSkill,
    SkillCategory,
    SkillReview,
    SkillStatus,
    SearchFilters,
    SearchResult,
)


class MarketplaceRegistry:
    """技能市场注册表

    管理技能、评价、下载统计
    """

    def __init__(self, db_path: str = ".young/marketplace.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Skills表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                version TEXT,
                latest_version TEXT,
                category TEXT,
                tags TEXT,
                author TEXT,
                author_email TEXT,
                author_url TEXT,
                repository_url TEXT,
                homepage TEXT,
                license TEXT,
                tarball_url TEXT,
                file_size INTEGER,
                download_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT,
                updated_at TEXT,
                published_at TEXT,
                manifest_json TEXT,
                engines TEXT
            )
        """)

        # Reviews表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                skill_id TEXT NOT NULL,
                skill_version TEXT,
                user_id TEXT,
                user_name TEXT,
                rating INTEGER,
                title TEXT,
                comment TEXT,
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (skill_id) REFERENCES skills(id)
            )
        """)

        # Downloads表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                skill_id TEXT NOT NULL,
                version TEXT,
                client_id TEXT,
                client_version TEXT,
                platform TEXT,
                downloaded_at TEXT,
                FOREIGN KEY (skill_id) REFERENCES skills(id)
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_skill ON reviews(skill_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_skill ON downloads(skill_id)")

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    # ========== Skills CRUD ==========

    def register_skill(self, skill: MarketplaceSkill) -> bool:
        """注册技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO skills (
                    id, name, display_name, description, version, latest_version,
                    category, tags, author, author_email, author_url,
                    repository_url, homepage, license, tarball_url, file_size,
                    download_count, rating, rating_count, status,
                    created_at, updated_at, published_at, manifest_json, engines
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                skill.id,
                skill.name,
                skill.display_name,
                skill.description,
                skill.version,
                skill.latest_version,
                skill.category.value if skill.category else None,
                json.dumps(skill.tags),
                skill.author,
                skill.author_email,
                skill.author_url,
                skill.repository_url,
                skill.homepage,
                skill.license,
                skill.tarball_url,
                skill.file_size,
                skill.download_count,
                skill.rating,
                skill.rating_count,
                skill.status.value if skill.status else None,
                skill.created_at.isoformat() if skill.created_at else None,
                skill.updated_at.isoformat() if skill.updated_at else None,
                skill.published_at.isoformat() if skill.published_at else None,
                json.dumps({}) if not skill.manifest else json.dumps(skill.manifest.__dict__),
                json.dumps(skill.engines),
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error registering skill: {e}")
            return False
        finally:
            conn.close()

    def get_skill(self, skill_id: str) -> Optional[MarketplaceSkill]:
        """获取技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_skill(row)

    def get_skill_by_name(self, name: str, version: str = None) -> Optional[MarketplaceSkill]:
        """根据名称和版本获取技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if version:
            cursor.execute(
                "SELECT * FROM skills WHERE name = ? AND version = ?",
                (name, version)
            )
        else:
            cursor.execute(
                "SELECT * FROM skills WHERE name = ? AND version = latest_version",
                (name,)
            )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_skill(row)

    def search_skills(self, filters: SearchFilters) -> SearchResult:
        """搜索技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建查询
        query = "SELECT * FROM skills WHERE status = 'published'"
        params = []

        if filters.query:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{filters.query}%", f"%{filters.query}%"])

        if filters.category:
            query += " AND category = ?"
            params.append(filters.category.value)

        if filters.min_rating > 0:
            query += " AND rating >= ?"
            params.append(filters.min_rating)

        # 排序
        if filters.sort_by == "downloads":
            query += " ORDER BY download_count"
        elif filters.sort_by == "rating":
            query += " ORDER BY rating"
        elif filters.sort_by == "newest":
            query += " ORDER BY published_at"
        else:
            query += " ORDER BY download_count"

        if filters.sort_order == "asc":
            query += " ASC"

        # 分页
        offset = (filters.page - 1) * filters.page_size
        query += f" LIMIT {filters.page_size} OFFSET {offset}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取总数
        count_query = query.replace(f" LIMIT {filters.page_size} OFFSET {offset}", "").replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        conn.close()

        skills = [self._row_to_skill(row) for row in rows]

        return SearchResult(
            skills=skills,
            total_count=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(total + filters.page_size - 1) // filters.page_size,
        )

    def list_skills(self, limit: int = 100) -> list[MarketplaceSkill]:
        """列出所有技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM skills ORDER BY download_count DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_skill(row) for row in rows]

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()

        return deleted

    def _row_to_skill(self, row: tuple) -> MarketplaceSkill:
        """将数据库行转换为MarketplaceSkill"""
        return MarketplaceSkill(
            id=row[0],
            name=row[1],
            display_name=row[2],
            description=row[3],
            version=row[4],
            latest_version=row[5],
            category=SkillCategory(row[6]) if row[6] else SkillCategory.CUSTOM,
            tags=json.loads(row[7]) if row[7] else [],
            author=row[8],
            author_email=row[9],
            author_url=row[10],
            repository_url=row[11],
            homepage=row[12],
            license=row[13],
            tarball_url=row[14],
            file_size=row[15] or 0,
            download_count=row[16] or 0,
            rating=row[17] or 0.0,
            rating_count=row[18] or 0,
            status=SkillStatus(row[19]) if row[19] else SkillStatus.DRAFT,
            created_at=datetime.fromisoformat(row[20]) if row[20] else datetime.now(),
            updated_at=datetime.fromisoformat(row[21]) if row[21] else datetime.now(),
            published_at=datetime.fromisoformat(row[22]) if row[22] else datetime.now(),
        )

    # ========== Reviews CRUD ==========

    def add_review(self, review: SkillReview) -> bool:
        """添加评价"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO reviews (
                    id, skill_id, skill_version, user_id, user_name,
                    rating, title, comment, helpful_count, not_helpful_count,
                    is_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review.id,
                review.skill_id,
                review.skill_version,
                review.user_id,
                review.user_name,
                review.rating,
                review.title,
                review.comment,
                review.helpful_count,
                review.not_helpful_count,
                1 if review.is_verified else 0,
                review.created_at.isoformat(),
                review.updated_at.isoformat(),
            ))
            conn.commit()

            # 更新技能评分
            self._update_skill_rating(review.skill_id)

            return True
        except Exception as e:
            logger.error(f"Error adding review: {e}")
            return False
        finally:
            conn.close()

    def get_reviews(self, skill_id: str, limit: int = 20) -> list[SkillReview]:
        """获取技能评价"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM reviews WHERE skill_id = ? ORDER BY created_at DESC LIMIT ?",
            (skill_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_review(row) for row in rows]

    def _row_to_review(self, row: tuple) -> SkillReview:
        """将数据库行转换为SkillReview"""
        return SkillReview(
            id=row[0],
            skill_id=row[1],
            skill_version=row[2],
            user_id=row[3],
            user_name=row[4],
            rating=row[5],
            title=row[6],
            comment=row[7],
            helpful_count=row[8] or 0,
            not_helpful_count=row[9] or 0,
            is_verified=bool(row[10]),
            created_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now(),
            updated_at=datetime.fromisoformat(row[12]) if row[12] else datetime.now(),
        )

    def _update_skill_rating(self, skill_id: str):
        """更新技能评分"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE skills
            SET rating = (
                SELECT AVG(rating) FROM reviews WHERE skill_id = ?
            ),
            rating_count = (
                SELECT COUNT(*) FROM reviews WHERE skill_id = ?
            )
            WHERE id = ?
        """, (skill_id, skill_id, skill_id))

        conn.commit()
        conn.close()

    # ========== Downloads ==========

    def record_download(self, skill_id: str, version: str, client_info: dict = None) -> bool:
        """记录下载"""
        import uuid

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            download_id = str(uuid.uuid4())
            client_id = client_info.get("client_id") if client_info else ""
            client_version = client_info.get("version") if client_info else ""
            platform = client_info.get("platform") if client_info else ""

            cursor.execute("""
                INSERT INTO downloads (id, skill_id, version, client_id, client_version, platform, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (download_id, skill_id, version, client_id, client_version, platform, datetime.now().isoformat()))

            # 更新下载计数
            cursor.execute(
                "UPDATE skills SET download_count = download_count + 1 WHERE id = ?",
                (skill_id,)
            )

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            return False
        finally:
            conn.close()

    # ========== Stats ==========

    def get_stats(self) -> dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM skills WHERE status = 'published'")
        total_skills = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(download_count) FROM skills")
        total_downloads = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(rating) FROM skills WHERE rating > 0")
        avg_rating = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]

        conn.close()

        return {
            "total_skills": total_skills,
            "total_downloads": total_downloads,
            "average_rating": round(avg_rating, 2),
            "total_reviews": total_reviews,
        }
