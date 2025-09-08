#!/usr/bin/env python3

# Simple test to check if our enhanced groundwater plugin works
import os
import sys
import pandas as pd

# Add the project directory to path
project_dir = os.path.join(os.path.dirname(__file__), 'project')
plugins_dir = os.path.join(project_dir, 'plugins', 'groundwater')
sys.path.insert(0, plugins_dir)
sys.path.insert(0, project_dir)

print("🧪 TESTING ENHANCED GROUNDWATER PLUGIN")
print("=" * 50)

try:
    from groundwater_plugin import answer_question
    
    # Test Chennai query
    print("\n📍 Testing: 'ground water data for chennai'")
    print("-" * 40)
    result = answer_question("ground water data for chennai")
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Checking plugin directory...")
    if os.path.exists(plugins_dir):
        files = os.listdir(plugins_dir)
        print(f"Files in {plugins_dir}: {files}")
    else:
        print(f"Directory {plugins_dir} does not exist")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
