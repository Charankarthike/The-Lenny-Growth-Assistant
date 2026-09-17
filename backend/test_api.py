"""
Quick API test script - verify endpoints work
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
from app.core.config import settings
from app.services.openai_service import get_openai_service
from app.models.chat import ChatRequest, Message


async def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI connection...")
    try:
        service = get_openai_service()
        response = await service.chat(
            messages=[
                {"role": "user", "content": "Say 'Hello from Lenny API' in exactly those words."}
            ],
            max_tokens=50
        )
        print(f"✅ OpenAI connection works!")
        print(f"   Response: {response[:100]}")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {str(e)}")
        return False


async def test_embeddings():
    """Test embedding generation"""
    print("\n🔍 Testing embeddings...")
    try:
        service = get_openai_service()
        embedding = await service.get_embedding("test text for embedding")
        print(f"✅ Embeddings work!")
        print(f"   Dimensions: {len(embedding)}")
        return True
    except Exception as e:
        print(f"❌ Embeddings failed: {str(e)}")
        return False


def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    try:
        print(f"   App: {settings.app_name}")
        print(f"   Environment: {settings.environment}")
        print(f"   LLM Model: {settings.llm_model}")
        print(f"   Embedding Model: {settings.embedding_model}")
        print(f"   Database URL: {settings.database_url[:30]}..." if settings.database_url else "   Database URL: NOT SET")
        print(f"   OpenAI Key: {'SET ✅' if settings.openai_api_key else 'NOT SET ❌'}")
        print(f"✅ Configuration loaded!")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {str(e)}")
        return False


def test_imports():
    """Test all imports work"""
    print("\n🔍 Testing imports...")
    try:
        from app.main import app
        from app.routes import chat, health
        from app.models.transcript import Transcript, TranscriptChunk
        from app.core.database import get_db, init_db
        from app.services.rag_service import get_rag_service
        print(f"✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 LENNY API TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test configuration
    results.append(("Configuration", test_config()))
    
    # Test OpenAI (only if API key is set)
    if settings.openai_api_key:
        results.append(("OpenAI Chat", await test_openai_connection()))
        results.append(("OpenAI Embeddings", await test_embeddings()))
    else:
        print("\n⚠️  Skipping OpenAI tests (no API key)")
        results.append(("OpenAI", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name:.<40} {status}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
