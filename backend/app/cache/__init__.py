from app.cache.client import redis_client
from app.cache.semantic_cache import SemanticCache


semantic_cache = SemanticCache(
    redis_client
)