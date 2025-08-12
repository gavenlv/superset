# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Cache manager for entitlement data."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from flask import current_app

from .entitlement_client import UserEntitlements, entitlement_client

logger = logging.getLogger(__name__)


class EntitlementCacheManager:
    """
    Multi-level cache manager for entitlement data.
    
    Provides L1 (memory) and L2 (Redis) caching for optimal performance.
    """
    
    def __init__(self):
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client if available."""
        try:
            # Try to import and initialize Redis
            import redis
            
            redis_url = current_app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except ImportError:
            logger.warning("Redis not available, using memory cache only")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}, using memory cache only")
            self.redis_client = None
    
    def get_user_entitlements(self, user_id: str) -> Optional[UserEntitlements]:
        """
        Get user entitlements with multi-level caching.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserEntitlements object or None
        """
        try:
            # Level 1: Memory cache (fastest)
            cache_key = f"entitlements:{user_id}"
            
            if cache_key in self.memory_cache:
                cached_data = self.memory_cache[cache_key]
                if not self._is_expired(cached_data):
                    logger.debug(f"Memory cache hit for user {user_id}")
                    return self._deserialize_entitlements(cached_data['data'])
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
            
            # Level 2: Redis cache
            if self.redis_client:
                try:
                    cached_json = self.redis_client.get(cache_key)
                    if cached_json:
                        cached_data = json.loads(cached_json)
                        if not self._is_expired(cached_data):
                            logger.debug(f"Redis cache hit for user {user_id}")
                            # Store in memory cache for faster access
                            self.memory_cache[cache_key] = cached_data
                            return self._deserialize_entitlements(cached_data['data'])
                        else:
                            # Remove expired entry
                            self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis cache error: {e}")
            
            # Level 3: Fetch from entitlement service
            logger.debug(f"Cache miss for user {user_id}, fetching from service")
            entitlements = entitlement_client.fetch_user_entitlements(user_id)
            
            if entitlements:
                self._cache_entitlements(user_id, entitlements)
                return entitlements
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get entitlements for user {user_id}: {e}")
            return None
    
    def _cache_entitlements(self, user_id: str, entitlements: UserEntitlements) -> None:
        """
        Store entitlements in cache.
        
        Args:
            user_id: User identifier
            entitlements: UserEntitlements object
        """
        try:
            cache_key = f"entitlements:{user_id}"
            cache_data = {
                'data': self._serialize_entitlements(entitlements),
                'timestamp': time.time(),
                'ttl': entitlements.cache_ttl
            }
            
            # Store in memory cache
            self.memory_cache[cache_key] = cache_data
            
            # Store in Redis cache
            if self.redis_client:
                try:
                    cache_json = json.dumps(cache_data)
                    self.redis_client.setex(
                        cache_key, 
                        entitlements.cache_ttl,
                        cache_json
                    )
                    logger.debug(f"Cached entitlements for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to cache in Redis: {e}")
            
        except Exception as e:
            logger.error(f"Failed to cache entitlements for user {user_id}: {e}")
    
    def invalidate_user_cache(self, user_id: str) -> None:
        """
        Invalidate cache for a specific user.
        
        Args:
            user_id: User identifier
        """
        cache_key = f"entitlements:{user_id}"
        
        # Remove from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # Remove from Redis cache
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                logger.info(f"Invalidated cache for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to invalidate Redis cache: {e}")
    
    def invalidate_role_cache(self, role_name: str) -> None:
        """
        Invalidate cache for all users with a specific role.
        
        Args:
            role_name: Role name
        """
        try:
            # Find all users with this role and invalidate their cache
            users_with_role = self._get_users_by_role(role_name)
            
            for user_id in users_with_role:
                self.invalidate_user_cache(user_id)
            
            logger.info(f"Invalidated cache for role {role_name} ({len(users_with_role)} users)")
            
        except Exception as e:
            logger.error(f"Failed to invalidate role cache: {e}")
    
    def clear_all_cache(self) -> None:
        """Clear all cached entitlements."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear Redis cache
        if self.redis_client:
            try:
                # Find all entitlement keys
                keys = self.redis_client.keys("entitlements:*")
                if keys:
                    self.redis_client.delete(*keys)
                logger.info("Cleared all entitlement cache")
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None,
            'redis_cache_size': 0
        }
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys("entitlements:*")
                stats['redis_cache_size'] = len(keys)
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        return stats
    
    def _serialize_entitlements(self, entitlements: UserEntitlements) -> Dict[str, Any]:
        """Serialize UserEntitlements to dictionary."""
        return {
            'user_id': entitlements.user_id,
            'roles': entitlements.roles,
            'permissions': entitlements.permissions,
            'row_level_filters': entitlements.row_level_filters,
            'cache_ttl': entitlements.cache_ttl
        }
    
    def _deserialize_entitlements(self, data: Dict[str, Any]) -> UserEntitlements:
        """Deserialize dictionary to UserEntitlements."""
        return UserEntitlements(
            user_id=data['user_id'],
            roles=data.get('roles', []),
            permissions=data.get('permissions', {}),
            row_level_filters=data.get('row_level_filters', {}),
            cache_ttl=data.get('cache_ttl', 300)
        )
    
    def _is_expired(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is expired."""
        timestamp = cached_data.get('timestamp', 0)
        ttl = cached_data.get('ttl', 300)
        return time.time() - timestamp > ttl
    
    def _get_users_by_role(self, role_name: str) -> List[str]:
        """
        Get list of users with a specific role.
        
        This is a simplified implementation. In a real system,
        this would query the user management system.
        
        Args:
            role_name: Role name
            
        Returns:
            List of user IDs
        """
        users_with_role = []
        
        # Check memory cache for users with this role
        for cache_key, cached_data in self.memory_cache.items():
            if cache_key.startswith('entitlements:'):
                try:
                    entitlements_data = cached_data['data']
                    if role_name in entitlements_data.get('roles', []):
                        user_id = entitlements_data['user_id']
                        users_with_role.append(user_id)
                except Exception as e:
                    logger.error(f"Error checking role for cached user: {e}")
        
        return users_with_role


class CacheInvalidationManager:
    """
    Manager for cache invalidation operations.
    """
    
    def __init__(self, cache_manager: EntitlementCacheManager):
        self.cache_manager = cache_manager
    
    def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate cache for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache_manager.invalidate_user_cache(user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            return False
    
    def invalidate_role_cache(self, role_name: str) -> bool:
        """
        Invalidate cache for all users with a role.
        
        Args:
            role_name: Role name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache_manager.invalidate_role_cache(role_name)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate role cache: {e}")
            return False
    
    def refresh_cache(self, user_ids: List[str] = None) -> Dict[str, bool]:
        """
        Refresh cache for specified users or all cached users.
        
        Args:
            user_ids: List of user IDs to refresh, or None for all
            
        Returns:
            Dictionary mapping user IDs to success status
        """
        results = {}
        
        if user_ids is None:
            # Get all cached user IDs
            user_ids = []
            for cache_key in self.cache_manager.memory_cache.keys():
                if cache_key.startswith('entitlements:'):
                    user_id = cache_key.replace('entitlements:', '')
                    user_ids.append(user_id)
        
        for user_id in user_ids:
            try:
                # Invalidate existing cache
                self.cache_manager.invalidate_user_cache(user_id)
                
                # Fetch fresh data
                entitlements = entitlement_client.fetch_user_entitlements(user_id)
                if entitlements:
                    self.cache_manager._cache_entitlements(user_id, entitlements)
                    results[user_id] = True
                else:
                    results[user_id] = False
                    
            except Exception as e:
                logger.error(f"Failed to refresh cache for user {user_id}: {e}")
                results[user_id] = False
        
        return results


# Global cache manager instances
cache_manager = EntitlementCacheManager()
cache_invalidation_manager = CacheInvalidationManager(cache_manager)


def get_user_entitlements(user_id: str) -> Optional[UserEntitlements]:
    """
    Get user entitlements (helper function).
    
    Args:
        user_id: User identifier
        
    Returns:
        UserEntitlements object or None
    """
    return cache_manager.get_user_entitlements(user_id)


def invalidate_user_cache(user_id: str) -> bool:
    """
    Invalidate cache for a user (helper function).
    
    Args:
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    return cache_invalidation_manager.invalidate_user_cache(user_id)


def invalidate_role_cache(role_name: str) -> bool:
    """
    Invalidate cache for a role (helper function).
    
    Args:
        role_name: Role name
        
    Returns:
        True if successful, False otherwise
    """
    return cache_invalidation_manager.invalidate_role_cache(role_name)


def init_cache_manager(app):
    """
    Initialize the cache manager.
    
    Args:
        app: Flask application instance
    """
    global cache_manager
    
    try:
        # Re-initialize with app context
        cache_manager._initialize_redis()
        logger.info("Cache manager initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize cache manager: {e}")


def setup_cache_cleanup():
    """Set up periodic cache cleanup (can be called from celery tasks)."""
    try:
        # Clean up expired entries from memory cache
        expired_keys = []
        for cache_key, cached_data in cache_manager.memory_cache.items():
            if cache_manager._is_expired(cached_data):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del cache_manager.memory_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}") 