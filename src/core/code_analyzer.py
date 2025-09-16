"""
Advanced Code Analyzer for DeepCode
Provides intelligent code analysis, AST parsing, and context extraction
"""

import ast
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import time

@dataclass
class CodeElement:
    """Represents a code element (function, class, variable, etc.)"""
    name: str
    type: str  # 'function', 'class', 'variable', 'import', 'method'
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    complexity: int = 0
    dependencies: List[str] = None

@dataclass
class FileAnalysis:
    """Complete analysis of a code file"""
    file_path: str
    language: str
    elements: List[CodeElement]
    imports: List[str]
    dependencies: List[str]
    complexity_score: int
    lines_of_code: int
    hash: str
    analysis_time: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]

class CodeAnalyzer:
    """Advanced code analyzer with AST parsing and intelligent analysis"""
    
    def __init__(self, config):
        self.config = config
        self.cache = {}  # Analysis cache for faster responses
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        # Language-specific analyzers
        self.analyzers = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.ts': self._analyze_typescript,
            '.java': self._analyze_java,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_c,
            '.go': self._analyze_go,
            '.rs': self._analyze_rust
        }
        
        # Common patterns for different languages
        self.patterns = {
            'function_patterns': {
                '.py': r'def\s+(\w+)\s*\(',
                '.js': r'function\s+(\w+)\s*\(|(\w+)\s*=\s*\(',
                '.ts': r'function\s+(\w+)\s*\(|(\w+)\s*=\s*\(',
                '.java': r'(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(',
                '.cpp': r'\w+\s+(\w+)\s*\(',
                '.c': r'\w+\s+(\w+)\s*\(',
                '.go': r'func\s+(\w+)\s*\(',
                '.rs': r'fn\s+(\w+)\s*\('
            },
            'class_patterns': {
                '.py': r'class\s+(\w+)',
                '.js': r'class\s+(\w+)',
                '.ts': r'class\s+(\w+)',
                '.java': r'class\s+(\w+)',
                '.cpp': r'class\s+(\w+)',
                '.c': r'struct\s+(\w+)',
                '.go': r'type\s+(\w+)\s+struct',
                '.rs': r'struct\s+(\w+)'
            }
        }

    def analyze_file(self, file_path: Path, force_refresh: bool = False) -> FileAnalysis:
        """Analyze a code file with caching for performance"""
        file_str = str(file_path)
        
        # Check cache first
        if not force_refresh and file_str in self.cache:
            cached_analysis, cache_time = self.cache[file_str]
            if time.time() - cache_time < self.cache_ttl:
                return cached_analysis
        
        start_time = time.time()
        
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Detect language
            language = self._detect_language(file_path.suffix)
            
            # Perform analysis based on file type
            analyzer = self.analyzers.get(file_path.suffix, self._analyze_generic)
            analysis = analyzer(file_path, content)
            
            # Calculate metrics
            lines_of_code = len([line for line in content.splitlines() if line.strip() and not line.strip().startswith('#')])
            complexity_score = self._calculate_complexity(content, file_path.suffix)
            
            # Detect issues and generate suggestions
            issues = self._detect_issues(content, language)
            suggestions = self._generate_suggestions(analysis, issues)
            
            # Create analysis result
            file_analysis = FileAnalysis(
                file_path=file_str,
                language=language,
                elements=analysis.get('elements', []),
                imports=analysis.get('imports', []),
                dependencies=analysis.get('dependencies', []),
                complexity_score=complexity_score,
                lines_of_code=lines_of_code,
                hash=file_hash,
                analysis_time=time.time() - start_time,
                issues=issues,
                suggestions=suggestions
            )
            
            # Cache the result
            self.cache[file_str] = (file_analysis, time.time())
            
            return file_analysis
            
        except Exception as e:
            # Return minimal analysis on error
            return FileAnalysis(
                file_path=file_str,
                language='unknown',
                elements=[],
                imports=[],
                dependencies=[],
                complexity_score=0,
                lines_of_code=0,
                hash='',
                analysis_time=time.time() - start_time,
                issues=[{'type': 'error', 'message': f'Analysis failed: {str(e)}'}],
                suggestions=[]
            )

    def _analyze_python(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Python code using AST"""
        elements = []
        imports = []
        dependencies = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function information
                    params = [arg.arg for arg in node.args.args]
                    docstring = ast.get_docstring(node)
                    
                    elements.append(CodeElement(
                        name=node.name,
                        type='function',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        docstring=docstring,
                        parameters=params,
                        complexity=self._calculate_function_complexity(node)
                    ))
                
                elif isinstance(node, ast.ClassDef):
                    # Extract class information
                    docstring = ast.get_docstring(node)
                    
                    elements.append(CodeElement(
                        name=node.name,
                        type='class',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        docstring=docstring
                    ))
                
                elif isinstance(node, ast.Import):
                    # Extract import information
                    for alias in node.names:
                        imports.append(alias.name)
                        dependencies.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    # Extract from import information
                    if node.module:
                        imports.append(node.module)
                        dependencies.append(node.module)
                        
        except SyntaxError as e:
            # Handle syntax errors gracefully
            pass
        
        return {
            'elements': elements,
            'imports': imports,
            'dependencies': dependencies
        }

    def _analyze_javascript(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code using regex patterns"""
        elements = []
        imports = []
        dependencies = []
        
        # Extract functions
        function_pattern = r'(?:function\s+(\w+)\s*\(|(\w+)\s*=\s*(?:function\s*\(|async\s*\(|\([^)]*\)\s*=>))'
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            func_name = match.group(1) or match.group(2)
            if func_name:
                line_num = content[:match.start()].count('\n') + 1
                elements.append(CodeElement(
                    name=func_name,
                    type='function',
                    line_start=line_num,
                    line_end=line_num
                ))
        
        # Extract classes
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            elements.append(CodeElement(
                name=class_name,
                type='class',
                line_start=line_num,
                line_end=line_num
            ))
        
        # Extract imports
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                module = match.group(1)
                imports.append(module)
                dependencies.append(module)
        
        return {
            'elements': elements,
            'imports': imports,
            'dependencies': dependencies
        }

    def _analyze_typescript(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze TypeScript code using regex patterns (similar to JavaScript)"""
        return self._analyze_javascript(file_path, content)

    def _analyze_java(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Java code using regex patterns"""
        return self._analyze_generic(file_path, content)

    def _analyze_cpp(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze C++ code using regex patterns"""
        return self._analyze_generic(file_path, content)

    def _analyze_c(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze C code using regex patterns"""
        return self._analyze_generic(file_path, content)

    def _analyze_go(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Go code using regex patterns"""
        return self._analyze_generic(file_path, content)

    def _analyze_rust(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze Rust code using regex patterns"""
        return self._analyze_generic(file_path, content)

    def _analyze_generic(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Generic analysis for unsupported languages"""
        elements = []
        imports = []
        dependencies = []
        
        extension = file_path.suffix
        
        # Try to extract functions using patterns
        if extension in self.patterns['function_patterns']:
            pattern = self.patterns['function_patterns'][extension]
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = None
                for group in match.groups():
                    if group:
                        func_name = group
                        break
                
                if func_name:
                    line_num = content[:match.start()].count('\n') + 1
                    elements.append(CodeElement(
                        name=func_name,
                        type='function',
                        line_start=line_num,
                        line_end=line_num
                    ))
        
        # Try to extract classes using patterns
        if extension in self.patterns['class_patterns']:
            pattern = self.patterns['class_patterns'][extension]
            for match in re.finditer(pattern, content, re.MULTILINE):
                class_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                elements.append(CodeElement(
                    name=class_name,
                    type='class',
                    line_start=line_num,
                    line_end=line_num
                ))
        
        return {
            'elements': elements,
            'imports': imports,
            'dependencies': dependencies
        }

    def _calculate_complexity(self, content: str, extension: str) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'case', 'switch']
        
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', content))
        
        return complexity

    def _calculate_function_complexity(self, node: ast.AST) -> int:
        """Calculate complexity for a specific function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                complexity += 1
        
        return complexity

    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(extension.lower(), 'unknown')

    def _detect_issues(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Detect common code issues"""
        issues = []
        
        # Common issues across languages
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'severity': 'warning',
                    'line': i,
                    'message': f'Line too long ({len(line)} characters)'
                })
            
            # TODO comments
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                issues.append({
                    'type': 'maintenance',
                    'severity': 'info',
                    'line': i,
                    'message': 'TODO/FIXME comment found'
                })
        
        # Language-specific issues
        if language == 'python':
            issues.extend(self._detect_python_issues(content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._detect_js_issues(content))
        
        return issues

    def _detect_python_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect Python-specific issues"""
        issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Missing docstrings for functions/classes
            if re.match(r'^\s*(def|class)\s+', line):
                # Check if next non-empty line is a docstring
                next_lines = lines[i:i+3]
                has_docstring = any('"""' in next_line or "'''" in next_line for next_line in next_lines)
                if not has_docstring:
                    issues.append({
                        'type': 'documentation',
                        'severity': 'warning',
                        'line': i,
                        'message': 'Missing docstring'
                    })
        
        return issues

    def _detect_js_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect JavaScript-specific issues"""
        issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Missing semicolons
            if re.search(r'[^;{}]\s*$', line.strip()) and line.strip() and not line.strip().endswith('{'):
                if any(keyword in line for keyword in ['var ', 'let ', 'const ', 'return ']):
                    issues.append({
                        'type': 'style',
                        'severity': 'info',
                        'line': i,
                        'message': 'Consider adding semicolon'
                    })
        
        return issues

    def _generate_suggestions(self, analysis: Dict[str, Any], issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        elements = analysis.get('elements', [])
        
        # Suggest adding docstrings
        functions_without_docs = [e for e in elements if e.type == 'function' and not e.docstring]
        if functions_without_docs:
            suggestions.append(f"Add docstrings to {len(functions_without_docs)} functions for better documentation")
        
        # Suggest breaking down complex functions
        complex_functions = [e for e in elements if e.complexity > 10]
        if complex_functions:
            suggestions.append(f"Consider refactoring {len(complex_functions)} complex functions (complexity > 10)")
        
        # Suggest based on issues
        error_count = len([i for i in issues if i.get('severity') == 'error'])
        warning_count = len([i for i in issues if i.get('severity') == 'warning'])
        
        if error_count > 0:
            suggestions.append(f"Fix {error_count} critical issues")
        if warning_count > 0:
            suggestions.append(f"Address {warning_count} warnings for better code quality")
        
        return suggestions

    def get_file_dependencies(self, file_path: Path) -> List[str]:
        """Get dependencies for a specific file"""
        analysis = self.analyze_file(file_path)
        return analysis.dependencies

    def detect_conflicts(self, file_path: Path, new_content: str) -> List[Dict[str, Any]]:
        """Detect potential conflicts when modifying a file"""
        conflicts = []
        
        try:
            # Analyze current file
            current_analysis = self.analyze_file(file_path)
            
            # Create temporary file for new content analysis
            temp_path = file_path.with_suffix(f'.temp{file_path.suffix}')
            temp_path.write_text(new_content)
            
            try:
                new_analysis = self.analyze_file(temp_path, force_refresh=True)
                
                # Compare function signatures
                current_functions = {e.name: e for e in current_analysis.elements if e.type == 'function'}
                new_functions = {e.name: e for e in new_analysis.elements if e.type == 'function'}
                
                # Check for removed functions
                for func_name in current_functions:
                    if func_name not in new_functions:
                        conflicts.append({
                            'type': 'removed_function',
                            'severity': 'error',
                            'message': f'Function "{func_name}" was removed',
                            'element': func_name
                        })
                
                # Check for signature changes
                for func_name in current_functions:
                    if func_name in new_functions:
                        current_func = current_functions[func_name]
                        new_func = new_functions[func_name]
                        
                        if current_func.parameters != new_func.parameters:
                            conflicts.append({
                                'type': 'signature_change',
                                'severity': 'warning',
                                'message': f'Function "{func_name}" signature changed',
                                'element': func_name
                            })
                
            finally:
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as e:
            conflicts.append({
                'type': 'analysis_error',
                'severity': 'error',
                'message': f'Could not analyze conflicts: {str(e)}'
            })
        
        return conflicts

    def clear_cache(self):
        """Clear the analysis cache"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_files': len(self.cache),
            'cache_ttl': self.cache_ttl,
            'memory_usage': sum(len(str(analysis)) for analysis, _ in self.cache.values())
        }