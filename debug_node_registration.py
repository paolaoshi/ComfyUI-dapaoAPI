import sys
import os
import traceback

# Add current directory to sys.path so we can import the module
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"Testing import of doubao_video_node from {current_dir}")

try:
    # Attempt to import the module
    import doubao_video_node
    print("✅ Module imported successfully")
    
    # Check for NODE_CLASS_MAPPINGS
    if hasattr(doubao_video_node, 'NODE_CLASS_MAPPINGS'):
        print("✅ NODE_CLASS_MAPPINGS found")
        print(f"   Content: {doubao_video_node.NODE_CLASS_MAPPINGS}")
    else:
        print("❌ NODE_CLASS_MAPPINGS NOT found in module")

    # Check for NODE_DISPLAY_NAME_MAPPINGS
    if hasattr(doubao_video_node, 'NODE_DISPLAY_NAME_MAPPINGS'):
        print("✅ NODE_DISPLAY_NAME_MAPPINGS found")
        print(f"   Content: {doubao_video_node.NODE_DISPLAY_NAME_MAPPINGS}")
    else:
        print("❌ NODE_DISPLAY_NAME_MAPPINGS NOT found in module")
        
except ImportError as e:
    print(f"❌ ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"❌ General Error: {e}")
    traceback.print_exc()
