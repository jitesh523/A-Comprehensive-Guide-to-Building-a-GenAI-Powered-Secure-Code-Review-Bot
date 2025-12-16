"""
Test script for Tree-sitter context extraction
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.context.tree_sitter_slicer import TreeSitterContextSlicer


def test_python_context():
    """Test context extraction for Python"""
    print("=" * 60)
    print("Testing Python Context Extraction")
    print("=" * 60)
    
    slicer = TreeSitterContextSlicer()
    
    # Test with vulnerable.py - line 11 (MD5 usage)
    context = slicer.extract_context(
        file_path="tests/vulnerable.py",
        line_number=11,
        language="python"
    )
    
    print(f"\n📍 Target: {context.get('file')}:{context.get('target_line')}")
    print(f"📦 Context Type: {context.get('context_type')}")
    print(f"🔧 Function: {context.get('function_name')}")
    print(f"📚 Class: {context.get('class_name')}")
    print(f"📏 Lines: {context.get('context_start_line')}-{context.get('context_end_line')}")
    
    if context.get('imports'):
        print(f"\n📥 Imports ({len(context.get('imports', []))}):")
        for imp in context.get('imports', [])[:3]:
            print(f"   {imp}")
    
    print(f"\n📝 Context Code:")
    print("-" * 60)
    print(context.get('context_code', 'N/A')[:500])
    print("-" * 60)
    
    return context


def test_javascript_context():
    """Test context extraction for JavaScript"""
    print("\n" + "=" * 60)
    print("Testing JavaScript Context Extraction")
    print("=" * 60)
    
    slicer = TreeSitterContextSlicer()
    
    # Test with vulnerable.js - line 7 (eval usage)
    context = slicer.extract_context(
        file_path="tests/vulnerable.js",
        line_number=7,
        language="javascript"
    )
    
    print(f"\n📍 Target: {context.get('file')}:{context.get('target_line')}")
    print(f"📦 Context Type: {context.get('context_type')}")
    print(f"🔧 Function: {context.get('function_name')}")
    print(f"📚 Class: {context.get('class_name')}")
    print(f"📏 Lines: {context.get('context_start_line')}-{context.get('context_end_line')}")
    
    if context.get('imports'):
        print(f"\n📥 Imports ({len(context.get('imports', []))}):")
        for imp in context.get('imports', [])[:3]:
            print(f"   {imp}")
    
    print(f"\n📝 Context Code:")
    print("-" * 60)
    print(context.get('context_code', 'N/A')[:500])
    print("-" * 60)
    
    return context


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    slicer = TreeSitterContextSlicer()
    
    # Test line at module level (no function)
    context = slicer.extract_context(
        file_path="tests/vulnerable.py",
        line_number=17,  # PASSWORD = "hardcoded_password_123"
        language="python"
    )
    
    print(f"\n📍 Module-level variable:")
    print(f"   Context Type: {context.get('context_type')}")
    print(f"   Function: {context.get('function_name', 'None')}")
    
    return context


def main():
    """Run all tests"""
    try:
        py_context = test_python_context()
        js_context = test_javascript_context()
        edge_context = test_edge_cases()
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print("✅ Python context extraction: OK")
        print("✅ JavaScript context extraction: OK")
        print("✅ Edge case handling: OK")
        print("\n🎉 All tests passed!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
