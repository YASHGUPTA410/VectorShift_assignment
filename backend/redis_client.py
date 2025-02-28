# redis_client.py

import os
import redis.asyncio as redis
import logging
from kombu.utils.url import safequote

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust logging level as needed

class RedisClient:
    """
    A wrapper class for asynchronous Redis operations.
    This class provides methods to add, retrieve, and delete key-value pairs.
    """
    def __init__(self, host: str = None, port: int = 6379, db: int = 0):
        # Use environment variable or default host, and ensure the host is URL safe
        host = host or os.environ.get('REDIS_HOST', 'localhost')
        safe_host = safequote(host)
        self._client = redis.Redis(host=safe_host, port=port, db=db)
        logger.info("Initialized Redis client with host=%s, port=%d, db=%d", safe_host, port, db)

    async def add_key_value(self, key: str, value: str, expire: int = None):
        """
        Set a key-value pair in Redis.
        
        Args:
            key (str): The key to set.
            value (str): The value to store.
            expire (int, optional): Expiration time in seconds.
        """
        logger.debug("Setting key: %s with expire: %s", key, expire)
        await self._client.set(key, value)
        if expire:
            await self._client.expire(key, expire)
        logger.debug("Key %s set successfully", key)

    async def get_value(self, key: str):
        """
        Retrieve the value of a given key from Redis.
        
        Args:
            key (str): The key to retrieve.
            
        Returns:
            The value associated with the key, or None if not found.
        """
        logger.debug("Retrieving key: %s", key)
        value = await self._client.get(key)
        logger.debug("Retrieved value for key %s: %s", key, value)
        return value

    async def delete_key(self, key: str):
        """
        Delete a key-value pair from Redis.
        
        Args:
            key (str): The key to delete.
        """
        logger.debug("Deleting key: %s", key)
        await self._client.delete(key)
        logger.debug("Key %s deleted successfully", key)

# Create a singleton instance of RedisClient for use in the application.
redis_client_instance = RedisClient()

# Helper functions that wrap the RedisClient methods for backward compatibility.

async def add_key_value_redis(key, value, expire=None):
    """
    Wrapper function to set a key-value pair in Redis.
    """
    await redis_client_instance.add_key_value(key, value, expire)

async def get_value_redis(key):
    """
    Wrapper function to retrieve a value from Redis by key.
    """
    return await redis_client_instance.get_value(key)

async def delete_key_redis(key):
    """
    Wrapper function to delete a key from Redis.
    """
    await redis_client_instance.delete_key(key)
