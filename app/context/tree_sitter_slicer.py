"""
Tree-sitter Context Extraction Engine

This module uses Tree-sitter to extract relevant code context around
security findings. It provides a unified API for both Python and JavaScript.
"""
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Node
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class TreeSitterContextSlicer:
    """
    Unified context extraction using Tree-sitter for Python and JavaScript.
    """
    
    def __init__(self):
        # Initialize parsers for both languages
        self.python_parser = Parser()
        self.python_parser.set_language(Language(tspython.language()))
        
        self.javascript_parser = Parser()
        self.javascript_parser.set_language(Language(tsjavascript.language()))
    
    def extract_context(
        self, 
        file_path: str, 
        line_number: int, 
        language: str,
        context_lines: int = 10
    ) -> Dict[str, Any]:
        """
        Extract code context around a specific line number.
        
        Args:
            file_path: Path to the source file
            line_number: Line number of the finding
            language: "python" or "javascript"
            context_lines: Number of lines to include before/after
            
        Returns:
            Dictionary containing extracted context
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse the source code
            parser = self._get_parser(language)
            tree = parser.parse(bytes(source_code, 'utf8'))
            
            # Find the node at the target line
            target_node = self._find_node_at_line(tree.root_node, line_number, source_code)
            
            if not target_node:
                # Fallback to simple line-based context
                return self._extract_line_context(source_code, line_number, context_lines)
            
            # Extract function/class containing the target line
            containing_function = self._find_containing_function(target_node, language)
            containing_class = self._find_containing_class(target_node, language)
            
            # Get the relevant code snippet
            if containing_function:
                context_node = containing_function
            elif containing_class:
                context_node = containing_class
            else:
                context_node = target_node
            
            # Extract source code for the context
            start_byte = context_node.start_byte
            end_byte = context_node.end_byte
            context_code = source_code[start_byte:end_byte]
            
            # Get line numbers
            start_line = context_node.start_point[0] + 1
            end_line = context_node.end_point[0] + 1
            
            return {
                "file": file_path,
                "target_line": line_number,
                "context_start_line": start_line,
                "context_end_line": end_line,
                "context_code": context_code,
                "context_type": self._get_node_type(context_node),
                "function_name": self._get_function_name(containing_function) if containing_function else None,
                "class_name": self._get_class_name(containing_class) if containing_class else None,
                "imports": self._extract_imports(tree.root_node, source_code, language)
            }
            
        except Exception as e:
            logger.error(f"Context extraction failed for {file_path}:{line_number} - {str(e)}")
            # Fallback to simple line-based context
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                return self._extract_line_context(source_code, line_number, context_lines)
            except:
                return {
                    "file": file_path,
                    "target_line": line_number,
                    "error": str(e)
                }
    
    def _get_parser(self, language: str) -> Parser:
        """Get the appropriate parser for the language."""
        if language.lower() == "python":
            return self.python_parser
        elif language.lower() in ["javascript", "js"]:
            return self.javascript_parser
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _find_node_at_line(self, node: Node, line_number: int, source_code: str) -> Optional[Node]:
        """
        Find the most specific node at the given line number.
        """
        # Convert to 0-indexed
        target_line = line_number - 1
        
        # Check if this node contains the target line
        if node.start_point[0] <= target_line <= node.end_point[0]:
            # Check children for more specific node
            for child in node.children:
                result = self._find_node_at_line(child, line_number, source_code)
                if result:
                    return result
            # No child contains it, return this node
            return node
        
        return None
    
    def _find_containing_function(self, node: Node, language: str) -> Optional[Node]:
        """
        Find the function definition containing this node.
        """
        function_types = {
            "python": ["function_definition", "async_function_definition"],
            "javascript": ["function_declaration", "function_expression", "arrow_function", "method_definition"]
        }
        
        target_types = function_types.get(language.lower(), [])
        
        current = node
        while current:
            if current.type in target_types:
                return current
            current = current.parent
        
        return None
    
    def _find_containing_class(self, node: Node, language: str) -> Optional[Node]:
        """
        Find the class definition containing this node.
        """
        class_types = {
            "python": ["class_definition"],
            "javascript": ["class_declaration", "class_expression"]
        }
        
        target_types = class_types.get(language.lower(), [])
        
        current = node
        while current:
            if current.type in target_types:
                return current
            current = current.parent
        
        return None
    
    def _get_node_type(self, node: Node) -> str:
        """Get human-readable node type."""
        return node.type
    
    def _get_function_name(self, node: Optional[Node]) -> Optional[str]:
        """Extract function name from function node."""
        if not node:
            return None
        
        # Look for identifier child
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode('utf8')
        
        return None
    
    def _get_class_name(self, node: Optional[Node]) -> Optional[str]:
        """Extract class name from class node."""
        if not node:
            return None
        
        # Look for identifier child
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode('utf8')
        
        return None
    
    def _extract_imports(self, root_node: Node, source_code: str, language: str) -> List[str]:
        """
        Extract import statements from the file.
        """
        imports = []
        
        import_types = {
            "python": ["import_statement", "import_from_statement"],
            "javascript": ["import_statement", "import_declaration"]
        }
        
        target_types = import_types.get(language.lower(), [])
        
        def traverse(node: Node):
            if node.type in target_types:
                start = node.start_byte
                end = node.end_byte
                import_text = source_code[start:end]
                imports.append(import_text)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return imports[:10]  # Limit to first 10 imports
    
    def _extract_line_context(
        self, 
        source_code: str, 
        line_number: int, 
        context_lines: int
    ) -> Dict[str, Any]:
        """
        Fallback: Extract simple line-based context.
        """
        lines = source_code.split('\n')
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)
        
        context_code = '\n'.join(lines[start_line:end_line])
        
        return {
            "target_line": line_number,
            "context_start_line": start_line + 1,
            "context_end_line": end_line,
            "context_code": context_code,
            "context_type": "line_based_fallback"
        }
