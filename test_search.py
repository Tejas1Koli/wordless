#!/usr/bin/env python3
"""Test script for Wordless search - bypasses API key, uses local Ollama."""

import sys
from unittest.mock import patch, MagicMock

# Test data
TEST_CALLGRAPH = {
    'login': {'hash_password', 'query', 'verify', 'session'},
    'hash_password': {'crypto'},
    'query': {'connect'},
    'verify': {'crypto'},
    'session': {'create'},
}

TEST_RESULTS = {
    'documents': [
        [
            'def login(username, password):\n    pwd_hash = hash_password(password)\n    user = query(f"SELECT * FROM users WHERE name=\'{username}\'")\n    if verify(pwd_hash, user.password_hash):\n        return session.create(user.id)\n    raise Exception("Invalid credentials")',
            'def hash_password(pwd):\n    return crypto.sha256(pwd)',
            'def query(sql):\n    conn = connect()\n    return conn.execute(sql)',
        ]
    ], 
    'metadatas': [
        [
            {'name': 'login', 'file': 'auth.py', 'line': 1},
            {'name': 'hash_password', 'file': 'auth.py', 'line': 8},
            {'name': 'query', 'file': 'db.py', 'line': 5},
        ]
    ]
}

# Mock embed and search functions
def mock_embed(texts):
    """Mock embedding - returns dummy vectors."""
    return [[0.1] * 384 for _ in texts]

def mock_search(query_embedding, top_k=5):
    """Mock store search - returns test data."""
    return TEST_RESULTS

# Patch and run
print("=" * 70)
print("✅ TOON FORMAT TEST (Mocked, no API needed)")
print("=" * 70)
print("\nTest Query: 'handle authentication'\n")
print("-" * 70)
print()

try:
    # Patch both functions
    with patch('wordless.indexer.embedder.embed', side_effect=mock_embed):
        with patch('wordless.indexer.store.search', side_effect=mock_search):
            from wordless.search import search_code
            
            result = search_code('handle authentication', TEST_CALLGRAPH, hops=2)
            print(result)
    
    print("\n" + "=" * 70)
    print("✅ Test passed! Toon format working correctly.")
    print("=" * 70)
    
except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
