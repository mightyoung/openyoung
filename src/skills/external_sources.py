"""
External Information Sources - 外部信息源集成

提供对外部信息源的统一访问：
- RSS/Atom 订阅源
- HackerNews API

基于成熟方案实现：
- RSS: 使用 feedparser 库 (https://github.com/kurtmckee/feedparser)
- HackerNews: 使用官方 Firebase API (https://github.com/HackerNews/API)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """信息源类型"""
    RSS = "rss"
    HACKERNEWS = "hackernews"


@dataclass
class NewsItem:
    """新闻条目"""
    id: str
    title: str
    url: Optional[str] = None
    source: str = ""
    published: Optional[datetime] = None
    score: int = 0
    author: Optional[str] = None
    summary: Optional[str] = None
    comments_count: int = 0
    raw_data: dict = field(default_factory=dict)


@dataclass
class SourceConfig:
    """信息源配置"""
    url: str
    source_type: SourceType
    enabled: bool = True
    max_items: int = 10
    keywords: list[str] = field(default_factory=list)  # 过滤关键词


@dataclass
class ExternalSourcesConfig:
    """外部信息源总配置"""
    sources: list[SourceConfig] = field(default_factory=list)
    timeout_seconds: int = 10
    user_agent: str = "OpenYoung/1.0 (External Source Fetcher)"

    @classmethod
    def default_config(cls) -> "ExternalSourcesConfig":
        """创建默认配置，包含常用技术源"""
        return cls(
            sources=[
                # HackerNews
                SourceConfig(
                    url="https://hacker-news.firebaseio.com/v0",
                    source_type=SourceType.HACKERNEWS,
                    max_items=15,
                ),
                # 知名技术 RSS 源
                SourceConfig(
                    url="https://news.ycombinator.com/rss",
                    source_type=SourceType.RSS,
                    max_items=10,
                ),
                SourceConfig(
                    url="https://www.technologyreview.com/feed/",
                    source_type=SourceType.RSS,
                    max_items=5,
                ),
                SourceConfig(
                    url="https:// WIRED.com/rss",
                    source_type=SourceType.RSS,
                    max_items=5,
                ),
            ],
            timeout_seconds=10,
        )


class HackerNewsClient:
    """HackerNews API 客户端

    使用官方 Firebase API: https://github.com/HackerNews/API
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, timeout: int = 10, user_agent: str = "OpenYoung/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    async def fetch_top_stories(self, limit: int = 10) -> list[NewsItem]:
        """获取 Top Stories"""
        import aiohttp

        items = []
        try:
            async with aiohttp.ClientSession() as session:
                # 获取 Top Stories IDs
                async with session.get(
                    f"{self.BASE_URL}/topstories.json",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": self.user_agent},
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"HN API returned {resp.status}")
                        return []
                    story_ids = await resp.json()

                # 获取前 N 个故事的详情
                for story_id in story_ids[:limit]:
                    item = await self._fetch_item(session, story_id)
                    if item:
                        items.append(item)

        except Exception as e:
            logger.error(f"Failed to fetch HN top stories: {e}")

        return items

    async def fetch_best_stories(self, limit: int = 10) -> list[NewsItem]:
        """获取 Best Stories"""
        import aiohttp

        items = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/beststories.json",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": self.user_agent},
                ) as resp:
                    if resp.status != 200:
                        return []
                    story_ids = await resp.json()

                for story_id in story_ids[:limit]:
                    item = await self._fetch_item(session, story_id)
                    if item:
                        items.append(item)

        except Exception as e:
            logger.error(f"Failed to fetch HN best stories: {e}")

        return items

    async def fetch_new_stories(self, limit: int = 10) -> list[NewsItem]:
        """获取 New Stories"""
        import aiohttp

        items = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/newstories.json",
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": self.user_agent},
                ) as resp:
                    if resp.status != 200:
                        return []
                    story_ids = await resp.json()

                for story_id in story_ids[:limit]:
                    item = await self._fetch_item(session, story_id)
                    if item:
                        items.append(item)

        except Exception as e:
            logger.error(f"Failed to fetch HN new stories: {e}")

        return items

    async def _fetch_item(self, session: aiohttp.ClientSession, item_id: int) -> Optional[NewsItem]:
        """获取单个故事详情"""
        try:
            async with session.get(
                f"{self.BASE_URL}/item/{item_id}.json",
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": self.user_agent},
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                if not data or data.get("type") != "story":
                    return None

                published = None
                if data.get("time"):
                    published = datetime.fromtimestamp(data["time"])

                return NewsItem(
                    id=str(data.get("id", "")),
                    title=data.get("title", ""),
                    url=data.get("url"),
                    source="HackerNews",
                    published=published,
                    score=data.get("score", 0),
                    author=data.get("by"),
                    summary=data.get("text"),
                    comments_count=data.get("descendants", 0),
                    raw_data=data,
                )
        except Exception as e:
            logger.debug(f"Failed to fetch HN item {item_id}: {e}")
            return None


class RSSClient:
    """RSS/Atom 订阅源客户端

    使用 feedparser 库解析 RSS/Atom 订阅源
    """

    def __init__(self, timeout: int = 10, user_agent: str = "OpenYoung/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    async def fetch_feed(self, url: str, limit: int = 10) -> list[NewsItem]:
        """获取 RSS 订阅源"""
        import aiohttp

        items = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": self.user_agent},
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"RSS fetch returned {resp.status} for {url}")
                        return []

                    content = await resp.text()

            # 解析 XML
            import feedparser

            parsed = feedparser.parse(content)

            source_name = self._extract_source_name(url, parsed)

            for entry in parsed.entries[:limit]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        from time import mktime

                        published = datetime.fromtimestamp(mktime(entry.published_parsed))
                    except Exception:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        from time import mktime

                        published = datetime.fromtimestamp(mktime(entry.updated_parsed))
                    except Exception:
                        pass

                # 获取 URL
                entry_url = getattr(entry, "link", None)
                if isinstance(entry_url, list):
                    entry_url = entry_url[0] if entry_url else None

                # 获取摘要
                summary = getattr(entry, "summary", None)
                if not summary and hasattr(entry, "description"):
                    summary = entry.description
                if isinstance(summary, list):
                    summary = summary[0] if summary else None

                items.append(
                    NewsItem(
                        id=getattr(entry, "id", entry_url or str(hash(entry.title))),
                        title=getattr(entry, "title", "Untitled"),
                        url=entry_url,
                        source=source_name,
                        published=published,
                        score=0,  # RSS 没有评分
                        author=getattr(entry, "author", None),
                        summary=summary,
                        comments_count=0,
                        raw_data=entry,
                    )
                )

        except ImportError:
            logger.warning("feedparser not installed, cannot parse RSS")
        except Exception as e:
            logger.error(f"Failed to fetch RSS {url}: {e}")

        return items

    def _extract_source_name(self, url: str, parsed) -> str:
        """从 URL 或解析结果中提取源名称"""
        # 尝试从解析结果获取
        if hasattr(parsed, "feed") and hasattr(parsed.feed, "title"):
            return parsed.feed.title

        # 从 URL 提取域名
        parsed_url = urlparse(url)
        return parsed_url.netloc.replace("www.", "")


class ExternalSourcesFetcher:
    """外部信息源获取器

    统一接口获取多种外部信息源
    """

    def __init__(self, config: Optional[ExternalSourcesConfig] = None):
        self.config = config or ExternalSourcesConfig.default_config()
        self._hn_client: Optional[HackerNewsClient] = None
        self._rss_client: Optional[RSSClient] = None

    @property
    def hn_client(self) -> HackerNewsClient:
        """获取 HN 客户端（延迟初始化）"""
        if self._hn_client is None:
            self._hn_client = HackerNewsClient(
                timeout=self.config.timeout_seconds,
                user_agent=self.config.user_agent,
            )
        return self._hn_client

    @property
    def rss_client(self) -> RSSClient:
        """获取 RSS 客户端（延迟初始化）"""
        if self._rss_client is None:
            self._rss_client = RSSClient(
                timeout=self.config.timeout_seconds,
                user_agent=self.config.user_agent,
            )
        return self._rss_client

    async def fetch_all(self, keywords: Optional[list[str]] = None) -> list[NewsItem]:
        """获取所有启用的信息源"""
        all_items = []

        # 并行获取所有源
        tasks = []
        for source in self.config.sources:
            if not source.enabled:
                continue

            if source.source_type == SourceType.HACKERNEWS:
                tasks.append(self._fetch_hackernews(source, keywords))
            elif source.source_type == SourceType.RSS:
                tasks.append(self._fetch_rss(source, keywords))

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Source fetch error: {result}")

        # 按发布时间排序
        all_items.sort(key=lambda x: x.published or datetime.min, reverse=True)

        return all_items

    async def _fetch_hackernews(
        self, source: SourceConfig, keywords: Optional[list[str]]
    ) -> list[NewsItem]:
        """获取 HackerNews"""
        # 获取 top stories
        items = await self.hn_client.fetch_top_stories(limit=source.max_items)

        # 关键词过滤
        if keywords:
            items = self._filter_by_keywords(items, keywords)

        return items

    async def _fetch_rss(
        self, source: SourceConfig, keywords: Optional[list[str]]
    ) -> list[NewsItem]:
        """获取 RSS 源"""
        items = await self.rss_client.fetch_feed(source.url, limit=source.max_items)

        # 关键词过滤
        if keywords:
            items = self._filter_by_keywords(items, keywords)

        return items

    def _filter_by_keywords(self, items: list[NewsItem], keywords: list[str]) -> list[NewsItem]:
        """按关键词过滤"""
        if not keywords:
            return items

        filtered = []
        keyword_lower = [k.lower() for k in keywords]

        for item in items:
            title_lower = item.title.lower()
            summary_lower = (item.summary or "").lower()

            # 标题或摘要包含任一关键词
            if any(k in title_lower or k in summary_lower for k in keyword_lower):
                filtered.append(item)

        return filtered


# 全局实例
_default_fetcher: Optional[ExternalSourcesFetcher] = None


def get_external_sources_fetcher(
    config: Optional[ExternalSourcesConfig] = None,
) -> ExternalSourcesFetcher:
    """获取全局外部信息源获取器"""
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = ExternalSourcesFetcher(config)
    return _default_fetcher
