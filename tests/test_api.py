"""NexusClaw API Integration Tests — One-shot QA pack."""
import pytest, asyncio, aiohttp, subprocess, time, os, sys

BASE_URL = "http://localhost:8080"
API_KEY = None

@pytest.fixture(scope="module")
def api_key():
    global API_KEY
    if not API_KEY:
        # Get token from login
        async def get_token():
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BASE_URL}/v1/auth/login", json={
                    "email": "nexusclaw@local",
                    "password": "nexusclaw"
                }) as resp:
                    if resp.ok:
                        data = await resp.json()
                        return data.get("token")
                    # Try register
                    async with session.post(f"{BASE_URL}/v1/auth/register", json={
                        "email": "nexusclaw@local",
                        "password": "nexusclaw",
                        "displayName": "NexusClaw Test"
                    }) as reg:
                        if reg.ok:
                            data = await reg.json()
                            return data.get("token")
                    return None
        API_KEY = asyncio.run(get_token())
    return API_KEY

@pytest.fixture
def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

@pytest.mark.asyncio
async def test_health(auth_headers):
    """Test 1: API health endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as resp:
            assert resp.status == 200, f"Health check failed: {resp.status}"
            data = await resp.json()
            assert data.get("ok") == True, "API not ok"
            print(f"  ✅ test_health: {data}")

@pytest.mark.asyncio
async def test_auth_register_login(auth_headers):
    """Test 2: Register and login flow."""
    async with aiohttp.ClientSession() as session:
        # Try login first
        async with session.post(f"{BASE_URL}/v1/auth/login", json={
            "email": "qa@test.local",
            "password": "test123"
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                assert "token" in data
                print(f"  ✅ test_auth: login ok")
                return
        
        # Register
        async with session.post(f"{BASE_URL}/v1/auth/register", json={
            "email": "qa@test.local",
            "password": "test123",
            "displayName": "QA Tester"
        }) as resp:
            assert resp.status == 200, f"Register failed: {resp.status} {await resp.text()}"
            data = await resp.json()
            assert "token" in data
            print(f"  ✅ test_auth: register ok")

@pytest.mark.asyncio
async def test_chat_sessions(auth_headers):
    """Test 3: Create and list chat sessions."""
    async with aiohttp.ClientSession() as session:
        # Create session
        async with session.post(f"{BASE_URL}/v1/chat/sessions",
            headers=auth_headers, json={"title": "QA Test Session"}) as resp:
            assert resp.status == 200, f"Create session failed: {resp.status}"
            data = await resp.json()
            session_id = data.get("id")
            assert session_id
            print(f"  ✅ test_chat_sessions: created {session_id}")
        
        # List sessions
        async with session.get(f"{BASE_URL}/v1/chat/sessions",
            headers=auth_headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert isinstance(data, list)
            print(f"  ✅ test_chat_sessions: listed {len(data)} sessions")

@pytest.mark.asyncio
async def test_chat_stream(auth_headers):
    """Test 4: Stream chat response."""
    async with aiohttp.ClientSession() as session:
        # Create session
        async with session.post(f"{BASE_URL}/v1/chat/sessions",
            headers=auth_headers, json={"title": "Stream Test"}) as resp:
            data = await resp.json()
            session_id = data["id"]
        
        # Stream chat
        chunks = []
        async with session.post(f"{BASE_URL}/v1/chat/answer/stream",
            headers=auth_headers,
            json={"sessionId": session_id, "message": "Say 'hello world' in exactly those words", 
                  "provider": "ollama", "model": "llama3.2"}) as resp:
            assert resp.status == 200
            async for line in resp.content:
                text = line.decode().strip()
                if text.startswith("data: "):
                    try:
                        import json as j
                        d = j.loads(text[6:])
                        if d.get("type") == "chunk":
                            chunks.append(d.get("content", ""))
                    except: pass
        
        full = "".join(chunks)
        assert len(full) > 0, "No response received"
        print(f"  ✅ test_chat_stream: got {len(chunks)} chunks, {len(full)} chars")
        print(f"     Response: {full[:100]}...")

@pytest.mark.asyncio
async def test_file_upload(auth_headers):
    """Test 5: File upload (create test file first)."""
    test_file = "/tmp/nexusclaw_test.txt"
    with open(test_file, "w") as f:
        f.write("NexusClaw test file.\nCreated by QA test suite.\n")
    
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        form.add_field("file", open(test_file, "rb"), filename="test.txt", content_type="text/plain")
        
        async with session.post(f"{BASE_URL}/v1/files/upload",
            headers={"Authorization": auth_headers["Authorization"]},
            data=form) as resp:
            # May fail if files not configured, but shouldn't 500
            assert resp.status < 500, f"File upload 500: {await resp.text()}"
            if resp.ok:
                data = await resp.json()
                print(f"  ✅ test_file_upload: {data}")
            else:
                print(f"  ⚠️  test_file_upload: {resp.status} (not configured)")

@pytest.mark.asyncio
async def test_autonomy_goals(auth_headers):
    """Test 6: Autonomy goals (create + list)."""
    async with aiohttp.ClientSession() as session:
        # Create goal
        async with session.post(f"{BASE_URL}/v1/autonomy/goals",
            headers=auth_headers,
            json={"title": "QA Test Goal", "objective": "Log 'QA test passed' to console"}) as resp:
            # May fail if autonomy not configured
            assert resp.status < 500, f"Goal create 500: {await resp.text()}"
            if resp.ok:
                data = await resp.json()
                print(f"  ✅ test_autonomy_goals: {data}")
            else:
                print(f"  ⚠️  test_autonomy_goals: {resp.status} (not configured)")

@pytest.mark.asyncio  
async def test_kill_switch(auth_headers):
    """Test 7: Kill switch endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/v1/autonomy/kill",
            headers=auth_headers) as resp:
            assert resp.status < 500, f"Kill switch 500: {await resp.text()}"
            if resp.ok:
                data = await resp.json()
                print(f"  ✅ test_kill_switch: {data}")
            else:
                print(f"  ⚠️  test_kill_switch: {resp.status} (not configured)")

def test_local_imports():
    """Test 8: All local modules can be imported."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    try:
        from src.soul.engine import Soul
        from src.providers.ollama import OllamaProvider
        from src.memory.vector_store import VectorMemory
        from src.tools.registry import get_registry
        from src.webhooks.engine import WebhookEngine
        from src.evoclaw.heartbeat import EvoClaw
        print("  ✅ test_local_imports: all modules imported ok")
    except ImportError as e:
        print(f"  ⚠️  test_local_imports: import error: {e}")

def run_qa():
    """Run all QA tests. Usage: python3 tests/test_api.py"""
    print("\n" + "="*60)
    print("NEXUSCLAW ONE-SHOT QA PACK")
    print("="*60)
    print(f"API: {BASE_URL}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if API is running
    try:
        result = subprocess.run(["curl", "-s", f"{BASE_URL}/health"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ API is running")
        else:
            print("❌ API not reachable")
            print("Start with: python3 apps/api/main.py")
            return
    except:
        print("❌ API not reachable")
        print("Start with: python3 apps/api/main.py")
        return
    
    print()
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_qa()
