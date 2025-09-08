import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'project', 'plugins', 'groundwater'))

from groundwater_plugin import GroundwaterPlugin

# Test the enhanced plugin
plugin = GroundwaterPlugin()

print("🧪 TESTING ENHANCED GROUNDWATER PLUGIN\n")
print("=" * 50)

# Test Chennai query
print("\n📍 Testing: 'ground water data for chennai'")
print("-" * 40)
result = plugin.call("ground water data for chennai")
print(result)

print("\n" + "=" * 50)

# Test another query  
print("\n📍 Testing: 'water availability in tamil nadu'")
print("-" * 40)
result2 = plugin.call("water availability in tamil nadu")
print(result2)
