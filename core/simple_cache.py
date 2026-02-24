"""
Simple in-memory TTL cache for expensive Firestore read operations.
Prevents re-querying the same data on every HTTP request within a short window.
This is NOT a distributed cache – it lives in the Django process memory.
"""
import time
import threading

_cache = {}
_lock = threading.Lock()

def get(key):
    """Return cached value if still fresh, else None."""
    with _lock:
        entry = _cache.get(key)
        if entry and time.time() < entry['expires']:
            return entry['value']
    return None

def set(key, value, ttl_seconds=300):
    """Store value in cache for ttl_seconds (default 5 minutes)."""
    with _lock:
        _cache[key] = {
            'value': value,
            'expires': time.time() + ttl_seconds
        }

def delete(key):
    """Invalidate a cache entry (call after writes)."""
    with _lock:
        _cache.pop(key, None)

def delete_prefix(prefix):
    """Invalidate all keys starting with prefix."""
    with _lock:
        keys_to_delete = [k for k in _cache if k.startswith(prefix)]
        for k in keys_to_delete:
            del _cache[k]
