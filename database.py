import redis
import json
import os
from datetime import timedelta

class RedisStorage:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        # Set default TTL to 24 hours
        self.default_ttl = timedelta(hours=24)

    def store_result(self, job_id, result):
        """Store result with expiration"""
        self.redis_client.setex(
            f"faq_job:{job_id}",
            self.default_ttl,
            json.dumps(result)
        )

    def get_result(self, job_id):
        """Get result by job ID"""
        result = self.redis_client.get(f"faq_job:{job_id}")
        return json.loads(result) if result else None

    def delete_result(self, job_id):
        """Delete result by job ID"""
        self.redis_client.delete(f"faq_job:{job_id}")

    def cleanup_expired(self):
        """Clean up expired jobs (Redis handles this automatically with TTL)"""
        pass

# Singleton instance
db = RedisStorage()