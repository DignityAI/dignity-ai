#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime

print("🚀 Dignity AI Content Generator Starting...")

# Check Python version
print(f"Python version: {sys.version}")

# Check for API key
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    print("❌ ERROR: CLAUDE_API_KEY environment variable not found")
    print("Available env vars:", [k for k in os.environ.keys() if 'CLAUDE' in k or 'API' in k])
    sys.exit(1)

print(f"✅ API key found: {api_key[:8]}...")

try:
    # Test anthropic import
    import anthropic
    print("✅ Anthropic library imported successfully")
    
    # Create simple test content
    test_content = {
        "generated_at": datetime.now().isoformat(),
        "framework": "Dignity Lens",
        "organization": "Defy Racism Collective",
        "status": "success",
        "message": "Basic generation test completed"
    }
    
    # Create output directory
    os.makedirs("generated_content", exist_ok=True)
    
    # Write test file
    with open("generated_content/test_output.json", "w") as f:
        json.dump(test_content, f, indent=2)
    
    print("✅ Test content generated successfully!")
    print("📁 Created: generated_content/test_output.json")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(2)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(2)

print("🎉 Script completed successfully!")
