#!/usr/bin/env python3
"""
Test Script for Desktop Development

Run this on your main machine to test the logic without e-paper hardware.
Uses mock display that saves images to /tmp.
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_terminal_mock():
    """Test terminal in windowed mode."""
    print("=" * 60)
    print("Testing Terminal (pygame windowed mode)")
    print("=" * 60)
    
    from display.terminal import Terminal
    import time
    
    term = Terminal(
        width=480,
        height=320,
        color_bg=(0, 0, 0),
        color_fg=(0, 255, 0),
        font_name="DejaVu Sans Mono",
        font_size=14,
        status_bar_height=32
    )
    
    # Test typing with delays
    term.set_status("testing", "hopeful")
    
    code = '''# hello from tiny programmer
# i am feeling hopeful today

def say_hello():
    print("it works!")

say_hello()
'''
    
    print("Typing code (watch the pygame window)...")
    term.type_string(code, delay_func=lambda: 0.05)
    
    # Keep window open briefly
    term.set_status("done", "proud")
    time.sleep(2)
    
    term.shutdown()
    print("Terminal test complete")
    print()


def test_llm_connection():
    """Test LLM server connection."""
    print("=" * 60)
    print("Testing LLM Connection")
    print("=" * 60)
    
    import requests
    
    endpoint = "http://localhost:8080/health"
    
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"✓ Server responding: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Server not running")
        print("  Start with: ./llama-server -m <model.gguf> --port 8080")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()


def test_llm_generation():
    """Test basic LLM generation."""
    print("=" * 60)
    print("Testing LLM Generation")
    print("=" * 60)
    
    import requests
    
    endpoint = "http://localhost:8080/completion"
    
    prompt = """You are a tiny programmer. Write a very short Python program (under 10 lines) that prints "Hello World" in an interesting way. Add a comment about how you feel.

```python
"""
    
    try:
        response = requests.post(endpoint, json={
            "prompt": prompt,
            "n_predict": 200,
            "temperature": 0.7,
            "stop": ["```"]
        }, timeout=60)
        
        result = response.json()
        print("Generated code:")
        print("-" * 40)
        print(result.get("content", "No content"))
        print("-" * 40)
    except requests.exceptions.ConnectionError:
        print("✗ Server not running")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()


def test_llm_streaming():
    """Test LLM streaming generation."""
    print("=" * 60)
    print("Testing LLM Streaming")
    print("=" * 60)
    
    import requests
    
    endpoint = "http://localhost:8080/completion"
    
    prompt = "# A tiny program\nprint('"
    
    try:
        response = requests.post(endpoint, json={
            "prompt": prompt,
            "n_predict": 50,
            "temperature": 0.7,
            "stream": True
        }, stream=True, timeout=60)
        
        print("Streaming tokens:")
        print("-" * 40)
        print(prompt, end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    import json
                    data = json.loads(line[6:])
                    content = data.get("content", "")
                    print(content, end="", flush=True)
                    if data.get("stop"):
                        break
        
        print()
        print("-" * 40)
    except requests.exceptions.ConnectionError:
        print("✗ Server not running")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()


def test_archive():
    """Test archive saving."""
    print("=" * 60)
    print("Testing Archive")
    print("=" * 60)
    
    from archive.repository import Repository
    import tempfile
    
    # Use temp directory for test
    test_path = tempfile.mkdtemp(prefix="tiny_programmer_test_")
    print(f"Test archive path: {test_path}")
    
    repo = Repository(local_path=test_path)
    
    # Save a test program
    code = '''# i made this!
print("hello from tiny programmer")
'''
    
    metadata = repo.save(
        code=code,
        program_type="test",
        mood="hopeful",
        success=True,
        thought_process="just testing"
    )
    
    print(f"✓ Saved program: {metadata.filename}")
    print(f"  ID: {metadata.id}")
    print(f"  Lines: {metadata.lines_of_code}")
    
    stats = repo.get_stats()
    print(f"  Total in archive: {stats['total_programs']}")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TINY PROGRAMMER - TEST SUITE")
    print("=" * 60 + "\n")
    
    test_terminal_mock()
    test_archive()
    test_llm_connection()
    
    # Only run generation tests if server is available
    import requests
    try:
        requests.get("http://localhost:8080/health", timeout=2)
        test_llm_generation()
        test_llm_streaming()
    except:
        print("Skipping LLM generation tests (server not running)")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
