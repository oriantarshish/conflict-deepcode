"""
Language detection utilities for DeepCode
Handles automatic detection of programming languages and file types
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class LanguageDetector:
    def __init__(self):
        self.file_extensions = {
            # Compiled languages
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.java': 'java',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.dart': 'dart',
            
            # Interpreted languages
            '.py': 'python',
            '.pyw': 'python',
            '.js': 'javascript',
            '.mjs': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.php': 'php',
            '.rb': 'ruby',
            '.pl': 'perl',
            '.pm': 'perl',
            '.lua': 'lua',
            '.r': 'r',
            '.R': 'r',
            '.jl': 'julia',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.psm1': 'powershell',
            
            # Web technologies
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.vue': 'vue',
            '.svelte': 'svelte',
            
            # Data formats
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.csv': 'csv',
            '.tsv': 'tsv',
            
            # Documentation
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.tex': 'latex',
            '.txt': 'text',
            
            # Configuration
            '.dockerfile': 'dockerfile',
            '.dockerignore': 'dockerignore',
            '.gitignore': 'gitignore',
            '.gitattributes': 'gitattributes',
            '.editorconfig': 'editorconfig',
            '.eslintrc': 'json',
            '.prettierrc': 'json',
            '.babelrc': 'json',
            
            # Database
            '.sql': 'sql',
            '.db': 'database',
            '.sqlite': 'database',
            '.sqlite3': 'database',
            
            # Other
            '.asm': 'assembly',
            '.s': 'assembly',
            '.S': 'assembly',
            '.makefile': 'makefile',
            '.cmake': 'cmake',
            '.gradle': 'gradle',
            '.maven': 'maven',
            '.pom': 'maven'
        }
        
        # Language-specific patterns for content detection
        self.content_patterns = {
            'python': [
                r'^#!/usr/bin/env python',
                r'^#!/usr/bin/python',
                r'^import\s+\w+',
                r'^from\s+\w+\s+import',
                r'^def\s+\w+\s*\(',
                r'^class\s+\w+',
                r'^if\s+__name__\s*==\s*["\']__main__["\']'
            ],
            'javascript': [
                r'^#!/usr/bin/env node',
                r'^const\s+\w+\s*=',
                r'^let\s+\w+\s*=',
                r'^var\s+\w+\s*=',
                r'^function\s+\w+\s*\(',
                r'^class\s+\w+',
                r'^import\s+.*\s+from\s+["\']',
                r'^require\s*\('
            ],
            'typescript': [
                r'^import\s+.*\s+from\s+["\']',
                r':\s*\w+\s*=',
                r':\s*\w+\s*\(',
                r'interface\s+\w+',
                r'type\s+\w+\s*=',
                r'export\s+(interface|type|class|function)'
            ],
            'java': [
                r'^package\s+\w+',
                r'^import\s+\w+',
                r'^public\s+class\s+\w+',
                r'^private\s+\w+\s+\w+',
                r'^public\s+static\s+void\s+main'
            ],
            'c': [
                r'^#include\s*<',
                r'^#include\s*"',
                r'^int\s+main\s*\(',
                r'^void\s+\w+\s*\(',
                r'^struct\s+\w+',
                r'^typedef\s+'
            ],
            'cpp': [
                r'^#include\s*<',
                r'^#include\s*"',
                r'^using\s+namespace\s+',
                r'^class\s+\w+',
                r'^std::',
                r'^template\s*<'
            ],
            'bash': [
                r'^#!/bin/bash',
                r'^#!/usr/bin/env bash',
                r'^\$\w+',
                r'^if\s+\[',
                r'^for\s+\w+\s+in',
                r'^while\s+\[',
                r'^function\s+\w+'
            ],
            'html': [
                r'^<!DOCTYPE\s+html',
                r'^<html',
                r'^<head>',
                r'^<body>',
                r'^<div\s+',
                r'^<script\s+',
                r'^<style\s+'
            ],
            'css': [
                r'^\s*\w+\s*\{',
                r'^@media\s+',
                r'^@import\s+',
                r'^@keyframes\s+',
                r'^\s*\.\w+',
                r'^\s*#\w+'
            ],
            'sql': [
                r'^SELECT\s+',
                r'^INSERT\s+INTO',
                r'^UPDATE\s+\w+\s+SET',
                r'^DELETE\s+FROM',
                r'^CREATE\s+TABLE',
                r'^ALTER\s+TABLE'
            ]
        }
    
    def detect_from_extension(self, file_path: str) -> Optional[str]:
        """Detect language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()
        return self.file_extensions.get(extension)
    
    def detect_from_content(self, content: str, file_path: str = None) -> Optional[str]:
        """Detect language from file content"""
        if not content:
            return None
        
        lines = content.split('\n')
        scores = {}
        
        # Check each language pattern
        for language, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                for line in lines[:20]:  # Check first 20 lines
                    if re.search(pattern, line, re.IGNORECASE):
                        score += 1
                        break  # Only count each pattern once
            
            if score > 0:
                scores[language] = score
        
        # Return language with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Fallback to extension detection
        if file_path:
            return self.detect_from_extension(file_path)
        
        return None
    
    def detect_language(self, file_path: str, content: str = None) -> Optional[str]:
        """Detect language using both extension and content"""
        # First try extension detection
        lang_from_ext = self.detect_from_extension(file_path)
        
        # If we have content, try content detection
        if content:
            lang_from_content = self.detect_from_content(content, file_path)
            
            # If both methods agree, return the result
            if lang_from_ext == lang_from_content:
                return lang_from_ext
            
            # If content detection found something, prefer it
            if lang_from_content:
                return lang_from_content
        
        # Fallback to extension detection
        return lang_from_ext
    
    def get_language_info(self, language: str) -> Dict[str, any]:
        """Get information about a programming language"""
        language_info = {
            'python': {
                'name': 'Python',
                'type': 'interpreted',
                'paradigm': ['object-oriented', 'functional', 'procedural'],
                'extensions': ['.py', '.pyw'],
                'shebang': '#!/usr/bin/env python3',
                'comment': '#',
                'indent': '4 spaces'
            },
            'javascript': {
                'name': 'JavaScript',
                'type': 'interpreted',
                'paradigm': ['object-oriented', 'functional', 'prototype-based'],
                'extensions': ['.js', '.mjs'],
                'comment': '//',
                'indent': '2 spaces'
            },
            'typescript': {
                'name': 'TypeScript',
                'type': 'compiled',
                'paradigm': ['object-oriented', 'functional'],
                'extensions': ['.ts', '.tsx'],
                'comment': '//',
                'indent': '2 spaces'
            },
            'java': {
                'name': 'Java',
                'type': 'compiled',
                'paradigm': ['object-oriented'],
                'extensions': ['.java'],
                'comment': '//',
                'indent': '4 spaces'
            },
            'cpp': {
                'name': 'C++',
                'type': 'compiled',
                'paradigm': ['object-oriented', 'procedural', 'generic'],
                'extensions': ['.cpp', '.cc', '.cxx', '.hpp'],
                'comment': '//',
                'indent': '4 spaces'
            },
            'c': {
                'name': 'C',
                'type': 'compiled',
                'paradigm': ['procedural'],
                'extensions': ['.c', '.h'],
                'comment': '//',
                'indent': '4 spaces'
            },
            'go': {
                'name': 'Go',
                'type': 'compiled',
                'paradigm': ['procedural', 'concurrent'],
                'extensions': ['.go'],
                'comment': '//',
                'indent': 'tab'
            },
            'rust': {
                'name': 'Rust',
                'type': 'compiled',
                'paradigm': ['systems', 'functional'],
                'extensions': ['.rs'],
                'comment': '//',
                'indent': '4 spaces'
            },
            'php': {
                'name': 'PHP',
                'type': 'interpreted',
                'paradigm': ['object-oriented', 'procedural'],
                'extensions': ['.php'],
                'comment': '//',
                'indent': '4 spaces'
            },
            'ruby': {
                'name': 'Ruby',
                'type': 'interpreted',
                'paradigm': ['object-oriented', 'functional'],
                'extensions': ['.rb'],
                'comment': '#',
                'indent': '2 spaces'
            }
        }
        
        return language_info.get(language, {
            'name': language.title(),
            'type': 'unknown',
            'paradigm': [],
            'extensions': [],
            'comment': '//',
            'indent': '4 spaces'
        })
    
    def get_supported_languages(self) -> List[str]:
        """Get list of all supported languages"""
        return list(self.file_extensions.values())
    
    def get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a specific language"""
        extensions = []
        for ext, lang in self.file_extensions.items():
            if lang == language:
                extensions.append(ext)
        return extensions
    
    def is_code_file(self, file_path: str) -> bool:
        """Check if file is likely a code file"""
        language = self.detect_from_extension(file_path)
        code_languages = {
            'python', 'javascript', 'typescript', 'jsx', 'tsx',
            'java', 'cpp', 'c', 'go', 'rust', 'php', 'ruby',
            'csharp', 'swift', 'kotlin', 'scala', 'dart',
            'html', 'css', 'scss', 'sass', 'less', 'vue',
            'sql', 'bash', 'powershell', 'assembly'
        }
        return language in code_languages
    
    def get_file_category(self, file_path: str) -> str:
        """Get category of file (code, config, data, docs, etc.)"""
        language = self.detect_from_extension(file_path)
        
        if language in ['python', 'javascript', 'typescript', 'jsx', 'tsx', 'java', 'cpp', 'c', 'go', 'rust', 'php', 'ruby', 'csharp', 'swift', 'kotlin', 'scala', 'dart']:
            return 'code'
        elif language in ['html', 'css', 'scss', 'sass', 'less', 'vue', 'svelte']:
            return 'web'
        elif language in ['json', 'yaml', 'yml', 'toml', 'ini', 'xml']:
            return 'config'
        elif language in ['sql', 'csv', 'tsv']:
            return 'data'
        elif language in ['md', 'rst', 'tex', 'txt']:
            return 'documentation'
        elif language in ['dockerfile', 'gitignore', 'gitattributes', 'editorconfig']:
            return 'project'
        else:
            return 'other'
