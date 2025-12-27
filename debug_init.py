import sys
import os
import traceback

# Add current directory to sys.path so we can import the module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# ComfyUI often imports custom nodes as 'custom_nodes.ComfyUI-dapaoAPI'
# or adds the custom_nodes dir to path and imports 'ComfyUI-dapaoAPI'
# Let's try to import __init__ directly by running it

print(f"Testing full __init__.py execution from {current_dir}")

try:
    # We need to mock 'server' module because __init__.py imports it
    # and it might not be available in this standalone script
    import types
    if 'server' not in sys.modules:
        mock_server = types.ModuleType('server')
        mock_prompt_server = types.ModuleType('PromptServer')
        mock_instance = types.SimpleNamespace()
        mock_instance.routes = types.SimpleNamespace()
        mock_instance.routes.get = lambda x: lambda y: y # Mock decorator
        mock_instance.routes.post = lambda x: lambda y: y # Mock decorator
        mock_instance.routes.put = lambda x: lambda y: y # Mock decorator
        mock_instance.routes.delete = lambda x: lambda y: y # Mock decorator
        
        mock_prompt_server.instance = mock_instance
        mock_server.PromptServer = mock_prompt_server
        sys.modules['server'] = mock_server
        print("✅ Mocked 'server' module for testing")

    # Also mock 'folder_paths' if needed by any imports
    if 'folder_paths' not in sys.modules:
        mock_folder_paths = types.ModuleType('folder_paths')
        mock_folder_paths.get_output_directory = lambda: "output"
        mock_folder_paths.get_temp_directory = lambda: "temp"
        mock_folder_paths.get_input_directory = lambda: "input"
        sys.modules['folder_paths'] = mock_folder_paths
        print("✅ Mocked 'folder_paths' module for testing")

    # Now import the package
    # We use importlib to import the current directory as a package
    import importlib.util
    spec = importlib.util.spec_from_file_location("ComfyUI-dapaoAPI", os.path.join(current_dir, "__init__.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["ComfyUI-dapaoAPI"] = module
    spec.loader.exec_module(module)
    
    print("\n---------------------------------------------------")
    print("Checking NODE_CLASS_MAPPINGS in __init__.py...")
    
    mappings = getattr(module, 'NODE_CLASS_MAPPINGS', {})
    display_mappings = getattr(module, 'NODE_DISPLAY_NAME_MAPPINGS', {})
    
    target_node = "DoubaoVideoGeneration"
    
    if target_node in mappings:
        print(f"✅ FOUND '{target_node}' in NODE_CLASS_MAPPINGS")
        print(f"   Class: {mappings[target_node]}")
    else:
        print(f"❌ FAILED: '{target_node}' NOT FOUND in NODE_CLASS_MAPPINGS")
        print("   Available keys:", list(mappings.keys()))

    if target_node in display_mappings:
        print(f"✅ FOUND '{target_node}' in NODE_DISPLAY_NAME_MAPPINGS")
        print(f"   Name: {display_mappings[target_node]}")
    else:
        print(f"❌ FAILED: '{target_node}' NOT FOUND in NODE_DISPLAY_NAME_MAPPINGS")
        
except ImportError as e:
    print(f"❌ ImportError during init execution: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"❌ General Error during init execution: {e}")
    traceback.print_exc()
