"""
Syntax highlighting utilities for DeepCode
Handles code syntax highlighting and formatting
"""

from typing import Optional, Dict, Any
from pathlib import Path
import re

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
    from pygments.formatters import TerminalFormatter, Terminal256Formatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

class SyntaxHighlighter:
    def __init__(self, use_colors: bool = True, style: str = 'monokai'):
        self.use_colors = use_colors
        self.style = style
        self.pygments_available = PYGMENTS_AVAILABLE
        
        # Fallback color mapping for basic highlighting
        self.color_map = {
            'keyword': '\033[95m',      # Magenta
            'string': '\033[92m',       # Green
            'comment': '\033[90m',      # Gray
            'number': '\033[94m',       # Blue
            'function': '\033[93m',     # Yellow
            'class': '\033[96m',        # Cyan
            'operator': '\033[91m',     # Red
            'reset': '\033[0m'          # Reset
        }
        
        # Language-specific patterns for fallback highlighting
        self.patterns = {
            'python': {
                'keywords': r'\b(and|as|assert|break|class|continue|def|del|elif|else|except|exec|finally|for|from|global|if|import|in|is|lambda|not|or|pass|print|raise|return|try|while|with|yield)\b',
                'strings': r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
                'comments': r'#.*$',
                'numbers': r'\b\d+(\.\d+)?\b',
                'functions': r'\bdef\s+(\w+)\s*\(',
                'classes': r'\bclass\s+(\w+)\s*[\(:]'
            },
            'javascript': {
                'keywords': r'\b(break|case|catch|class|const|continue|debugger|default|delete|do|else|export|extends|finally|for|function|if|import|in|instanceof|let|new|return|super|switch|this|throw|try|typeof|var|void|while|with|yield)\b',
                'strings': r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
                'comments': r'(//.*$|/\*.*?\*/)',
                'numbers': r'\b\d+(\.\d+)?\b',
                'functions': r'\bfunction\s+(\w+)\s*\(|(\w+)\s*:\s*function\s*\(',
                'classes': r'\bclass\s+(\w+)\s*[\(\{]'
            },
            'java': {
                'keywords': r'\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while)\b',
                'strings': r'("(?:[^"\\]|\\.)*")',
                'comments': r'(//.*$|/\*.*?\*/)',
                'numbers': r'\b\d+(\.\d+)?[fFdDlL]?\b',
                'functions': r'\b(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(',
                'classes': r'\b(public|private|protected)?\s*(abstract)?\s*class\s+(\w+)\s*[\(\{]'
            },
            'cpp': {
                'keywords': r'\b(alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|case|catch|char|char16_t|char32_t|class|compl|const|constexpr|const_cast|continue|decltype|default|delete|do|double|dynamic_cast|else|enum|explicit|export|extern|false|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|private|protected|public|register|reinterpret_cast|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|thread_local|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b',
                'strings': r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
                'comments': r'(//.*$|/\*.*?\*/)',
                'numbers': r'\b\d+(\.\d+)?[fFdDlL]?\b',
                'functions': r'\b\w+\s+(\w+)\s*\([^)]*\)\s*[\(\{]',
                'classes': r'\bclass\s+(\w+)\s*[\(\{]'
            },
            'html': {
                'tags': r'<(\w+)[^>]*>|</(\w+)>',
                'attributes': r'(\w+)=',
                'strings': r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
                'comments': r'<!--.*?-->'
            },
            'css': {
                'selectors': r'([.#]?\w+)\s*\{',
                'properties': r'(\w+)\s*:',
                'values': r':\s*([^;]+)',
                'comments': r'/\*.*?\*/'
            }
        }
    
    def highlight_code(self, code: str, language: str = None, filename: str = None) -> str:
        """Highlight code using Pygments or fallback method"""
        if self.pygments_available and self.use_colors:
            return self._highlight_with_pygments(code, language, filename)
        else:
            return self._highlight_fallback(code, language)
    
    def _highlight_with_pygments(self, code: str, language: str = None, filename: str = None) -> str:
        """Highlight code using Pygments"""
        try:
            # Try to get lexer
            lexer = None
            
            if filename:
                try:
                    lexer = guess_lexer_for_filename(filename, code)
                except ClassNotFound:
                    pass
            
            if not lexer and language:
                try:
                    lexer = get_lexer_by_name(language)
                except ClassNotFound:
                    pass
            
            if not lexer:
                # Fallback to text lexer
                lexer = get_lexer_by_name('text')
            
            # Choose formatter based on terminal capabilities
            if self.use_colors:
                try:
                    formatter = Terminal256Formatter(style=self.style)
                except:
                    formatter = TerminalFormatter()
            else:
                formatter = TerminalFormatter()
            
            return highlight(code, lexer, formatter)
            
        except Exception:
            # Fallback to basic highlighting
            return self._highlight_fallback(code, language)
    
    def _highlight_fallback(self, code: str, language: str = None) -> str:
        """Fallback highlighting using regex patterns"""
        if not self.use_colors or not language:
            return code
        
        patterns = self.patterns.get(language)
        if not patterns:
            return code
        
        lines = code.split('\n')
        highlighted_lines = []
        
        for line in lines:
            highlighted_line = line
            
            # Apply highlighting patterns
            for pattern_type, pattern in patterns.items():
                if pattern_type == 'keywords':
                    highlighted_line = re.sub(pattern, f'{self.color_map["keyword"]}\\g<0>{self.color_map["reset"]}', highlighted_line, flags=re.IGNORECASE)
                elif pattern_type == 'strings':
                    highlighted_line = re.sub(pattern, f'{self.color_map["string"]}\\g<0>{self.color_map["reset"]}', highlighted_line)
                elif pattern_type == 'comments':
                    highlighted_line = re.sub(pattern, f'{self.color_map["comment"]}\\g<0>{self.color_map["reset"]}', highlighted_line)
                elif pattern_type == 'numbers':
                    highlighted_line = re.sub(pattern, f'{self.color_map["number"]}\\g<0>{self.color_map["reset"]}', highlighted_line)
                elif pattern_type == 'functions':
                    highlighted_line = re.sub(pattern, f'{self.color_map["function"]}\\g<0>{self.color_map["reset"]}', highlighted_line)
                elif pattern_type == 'classes':
                    highlighted_line = re.sub(pattern, f'{self.color_map["class"]}\\g<0>{self.color_map["reset"]}', highlighted_line)
            
            highlighted_lines.append(highlighted_line)
        
        return '\n'.join(highlighted_lines)
    
    def get_lexer_name(self, language: str) -> str:
        """Get Pygments lexer name for language"""
        lexer_map = {
            'python': 'python',
            'javascript': 'javascript',
            'typescript': 'typescript',
            'jsx': 'jsx',
            'tsx': 'tsx',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rust',
            'php': 'php',
            'ruby': 'ruby',
            'csharp': 'csharp',
            'swift': 'swift',
            'kotlin': 'kotlin',
            'scala': 'scala',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'sass': 'sass',
            'less': 'less',
            'sql': 'sql',
            'yaml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'markdown': 'markdown',
            'bash': 'bash',
            'shell': 'bash',
            'powershell': 'powershell',
            'dockerfile': 'dockerfile',
            'makefile': 'makefile',
            'cmake': 'cmake',
            'ini': 'ini',
            'toml': 'toml',
            'csv': 'csv',
            'diff': 'diff',
            'patch': 'diff'
        }
        return lexer_map.get(language.lower(), 'text')
    
    def format_code(self, code: str, language: str = None, max_width: int = 80) -> str:
        """Format code with basic formatting rules"""
        if not code:
            return code
        
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Basic line length limiting
            if len(line) > max_width:
                # Try to break at logical points
                if language == 'python':
                    # Break after commas, operators, etc.
                    if ',' in line:
                        parts = line.split(',')
                        current_line = parts[0]
                        for part in parts[1:]:
                            if len(current_line + ',' + part) <= max_width:
                                current_line += ',' + part
                            else:
                                formatted_lines.append(current_line + ',')
                                current_line = '    ' + part.strip()
                        formatted_lines.append(current_line)
                        continue
                
                # Fallback: just truncate with ellipsis
                formatted_lines.append(line[:max_width-3] + '...')
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def strip_colors(self, text: str) -> str:
        """Remove ANSI color codes from text"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def get_supported_languages(self) -> list:
        """Get list of languages with highlighting support"""
        if self.pygments_available:
            # This would require importing all lexers, which is expensive
            # Return a subset of common languages
            return [
                'python', 'javascript', 'typescript', 'jsx', 'tsx',
                'java', 'cpp', 'c', 'go', 'rust', 'php', 'ruby',
                'csharp', 'swift', 'kotlin', 'scala', 'dart',
                'html', 'css', 'scss', 'sass', 'less', 'vue',
                'sql', 'yaml', 'json', 'xml', 'markdown',
                'bash', 'powershell', 'dockerfile', 'makefile'
            ]
        else:
            return list(self.patterns.keys())
    
    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported for highlighting"""
        return language in self.get_supported_languages()
