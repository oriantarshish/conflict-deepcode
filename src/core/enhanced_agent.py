"""
Enhanced AI Agent for DeepCode
Super-intelligent agent with advanced memory, context analysis, and file management capabilities
"""

import json
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import time
import re
import os
import logging

from .ollama_client import OllamaClient, ChatMessage
from .file_manager import FileManager
from .context_builder import ContextBuilder
from .code_analyzer import CodeAnalyzer, FileAnalysis

@dataclass
class EnhancedMemory:
    """Advanced memory system for the agent"""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    file_operations: List[Dict[str, Any]] = field(default_factory=list)
    project_context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    session_context: Dict[str, Any] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)

@dataclass
class ContextAnalysis:
    """Comprehensive context analysis for intelligent decision making"""
    mentioned_files: List[str] = field(default_factory=list)
    referenced_functions: List[str] = field(default_factory=list)
    project_structure: Dict[str, Any] = field(default_factory=dict)
    code_patterns: List[str] = field(default_factory=list)
    user_intent: str = ""
    confidence_score: float = 0.0
    suggested_actions: List[str] = field(default_factory=list)

class EnhancedDeepCodeAgent:
    """Super-intelligent AI agent with advanced memory and analysis capabilities"""

    def __init__(self, config):
        self.config = config
        self.ollama = OllamaClient(config)
        self.file_manager = FileManager(config)
        self.context_builder = ContextBuilder(config)
        self.code_analyzer = CodeAnalyzer(config)

        # Enhanced memory system
        self.memory = EnhancedMemory()
        self.memory_file = Path.home() / '.deepcode' / 'enhanced_memory.json'
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_memory()

        # Advanced caching and performance
        self.response_cache = {}
        self.context_cache = {}
        self.analysis_cache = {}
        self.cache_ttl = timedelta(minutes=15)

        # Performance optimization
        self.max_context_length = config.get('agent.max_context_length', 8000)
        self.enable_streaming = config.get('agent.enable_streaming', True)
        self.enable_caching = config.get('agent.enable_caching', True)
        self.parallel_analysis = config.get('agent.parallel_analysis', True)

        # Thread pool for parallel operations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

        # Advanced analysis settings
        self.deep_analysis_enabled = True
        self.context_awareness_level = 3  # 1-5 scale
        self.memory_retention_days = 30

    def load_memory(self):
        """Load enhanced memory from persistent storage"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Load conversation history (last 100 entries)
                self.memory.conversation_history = data.get('conversation_history', [])[-100:]

                # Load file operations (last 50 entries)
                self.memory.file_operations = data.get('file_operations', [])[-50:]

                # Load project context
                self.memory.project_context = data.get('project_context', {})

                # Load user preferences
                self.memory.user_preferences = data.get('user_preferences', {})

                # Load learned patterns
                self.memory.learned_patterns = data.get('learned_patterns', {})

        except Exception as e:
            print(f"Warning: Could not load memory: {e}")

    def save_memory(self):
        """Save enhanced memory to persistent storage"""
        try:
            data = {
                'conversation_history': self.memory.conversation_history[-100:],
                'file_operations': self.memory.file_operations[-50:],
                'project_context': self.memory.project_context,
                'user_preferences': self.memory.user_preferences,
                'learned_patterns': self.memory.learned_patterns,
                'last_saved': datetime.now().isoformat()
            }

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            print(f"Warning: Could not save memory: {e}")

    def analyze_message_context(self, message: str) -> ContextAnalysis:
        """Perform deep analysis of user message for context understanding"""
        analysis = ContextAnalysis()

        # Extract mentioned files
        analysis.mentioned_files = self._extract_file_mentions(message)

        # Extract referenced functions/classes
        analysis.referenced_functions = self._extract_function_references(message)

        # Analyze project structure if files are mentioned
        if analysis.mentioned_files:
            analysis.project_structure = self._analyze_project_structure(analysis.mentioned_files)

        # Detect code patterns in the message
        analysis.code_patterns = self._detect_code_patterns(message)

        # Determine user intent
        analysis.user_intent = self._classify_user_intent(message)

        # Calculate confidence score
        analysis.confidence_score = self._calculate_intent_confidence(message, analysis)

        # Generate suggested actions
        analysis.suggested_actions = self._generate_suggested_actions(message, analysis)

        return analysis

    def _extract_file_mentions(self, message: str) -> List[str]:
        """Extract all file mentions from the message"""
        files = []

        # File extensions pattern
        file_pattern = r'(\w+(?:/\w+)*\.(?:py|js|ts|java|cpp|c|go|rs|php|rb|cs|swift|kt|scala|html|css|json|yaml|yml|md|txt))'
        matches = re.findall(file_pattern, message, re.IGNORECASE)
        files.extend(matches)

        # Directory patterns
        dir_pattern = r'(\w+(?:/\w+)*/?)'
        dir_matches = re.findall(dir_pattern, message)
        # Filter out common words
        common_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'and', 'or'}
        dirs = [d for d in dir_matches if d not in common_words and len(d) > 2]
        files.extend(dirs)

        return list(set(files))  # Remove duplicates

    def _extract_function_references(self, message: str) -> List[str]:
        """Extract function and class references from message"""
        references = []

        # Function patterns
        func_patterns = [
            r'function\s+(\w+)',
            r'def\s+(\w+)',
            r'class\s+(\w+)',
            r'method\s+(\w+)',
            r'(\w+)\s*\(',
        ]

        for pattern in func_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))

    def _analyze_project_structure(self, mentioned_files: List[str]) -> Dict[str, Any]:
        """Analyze project structure around mentioned files"""
        structure = {
            'root_directory': str(Path.cwd()),
            'mentioned_files_exist': [],
            'related_files': [],
            'project_type': 'unknown',
            'languages': set()
        }

        for file_path in mentioned_files:
            path = Path(file_path)
            if path.exists():
                structure['mentioned_files_exist'].append(str(path))
                structure['languages'].add(path.suffix)

                # Find related files
                related = self.file_manager.find_similar_files(path)
                structure['related_files'].extend([str(f) for f in related])

        # Determine project type
        if '.py' in structure['languages']:
            structure['project_type'] = 'python'
        elif any(ext in structure['languages'] for ext in ['.js', '.ts']):
            structure['project_type'] = 'javascript'
        elif '.java' in structure['languages']:
            structure['project_type'] = 'java'

        return structure

    def _detect_code_patterns(self, message: str) -> List[str]:
        """Detect coding patterns and keywords in the message"""
        patterns = []

        # Programming keywords
        keywords = [
            'function', 'class', 'method', 'variable', 'import', 'export',
            'async', 'await', 'try', 'catch', 'if', 'else', 'for', 'while',
            'return', 'yield', 'lambda', 'decorator', 'interface', 'enum'
        ]

        for keyword in keywords:
            if keyword in message.lower():
                patterns.append(keyword)

        # Code structures
        if '{' in message and '}' in message:
            patterns.append('code_block')
        if '```' in message:
            patterns.append('markdown_code')

        return patterns

    def _classify_user_intent(self, message: str) -> str:
        """Classify the user's intent from the message"""
        message_lower = message.lower()

        # File operations
        if any(word in message_lower for word in ['create', 'make', 'new', 'add']):
            if 'file' in message_lower or 'folder' in message_lower:
                return 'create_file_folder'

        if any(word in message_lower for word in ['edit', 'modify', 'change', 'update']):
            return 'edit_file'

        if any(word in message_lower for word in ['read', 'show', 'display', 'view']):
            return 'read_file'

        if any(word in message_lower for word in ['delete', 'remove', 'erase']):
            return 'delete_file'

        # Code analysis
        if any(word in message_lower for word in ['analyze', 'review', 'check', 'examine']):
            return 'analyze_code'

        if any(word in message_lower for word in ['explain', 'understand', 'what does']):
            return 'explain_code'

        # General coding
        if any(word in message_lower for word in ['code', 'program', 'script', 'function']):
            return 'coding_task'

        return 'general_chat'

    def _calculate_intent_confidence(self, message: str, analysis: ContextAnalysis) -> float:
        """Calculate confidence score for intent classification"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on specific keywords
        intent_keywords = {
            'create_file_folder': ['create', 'new', 'make', 'add', 'folder', 'directory'],
            'edit_file': ['edit', 'modify', 'change', 'update', 'fix', 'improve'],
            'read_file': ['read', 'show', 'display', 'view', 'open'],
            'delete_file': ['delete', 'remove', 'erase'],
            'analyze_code': ['analyze', 'review', 'check', 'examine', 'test'],
            'explain_code': ['explain', 'understand', 'what', 'how'],
            'coding_task': ['code', 'program', 'script', 'function', 'class']
        }

        intent = analysis.user_intent
        if intent in intent_keywords:
            keywords = intent_keywords[intent]
            matches = sum(1 for keyword in keywords if keyword in message.lower())
            confidence += matches * 0.1

        # Increase confidence based on file mentions
        if analysis.mentioned_files:
            confidence += 0.2

        # Increase confidence based on code patterns
        if analysis.code_patterns:
            confidence += len(analysis.code_patterns) * 0.05

        return min(confidence, 1.0)

    def _generate_suggested_actions(self, message: str, analysis: ContextAnalysis) -> List[str]:
        """Generate suggested actions based on context analysis"""
        suggestions = []

        if analysis.user_intent == 'create_file_folder':
            suggestions.append("Create the specified file or folder")
            if analysis.mentioned_files:
                suggestions.append(f"Check if {analysis.mentioned_files[0]} already exists")

        elif analysis.user_intent == 'edit_file':
            if analysis.mentioned_files:
                suggestions.append(f"Read and analyze {analysis.mentioned_files[0]} before editing")
                suggestions.append("Create backup before making changes")
            suggestions.append("Validate changes after editing")

        elif analysis.user_intent == 'read_file':
            if analysis.mentioned_files:
                suggestions.append(f"Display contents of {analysis.mentioned_files[0]}")
            suggestions.append("Provide file analysis and summary")

        elif analysis.user_intent == 'analyze_code':
            suggestions.append("Perform comprehensive code analysis")
            suggestions.append("Check for potential issues and improvements")
            suggestions.append("Generate suggestions for optimization")

        return suggestions

    def enhanced_chat(self, message: str, context: Dict[str, Any] = None) -> str:
        """Enhanced chat with super-intelligent context analysis and memory"""
        start_time = time.time()

        try:
            # Step 1: Deep context analysis
            context_analysis = self.analyze_message_context(message)

            # Step 2: Update memory with current interaction
            self._update_memory(message, context_analysis)

            # Step 3: Retrieve relevant historical context
            historical_context = self._retrieve_relevant_context(message, context_analysis)

            # Step 4: Analyze project state if relevant
            project_analysis = self._analyze_current_project_state(context_analysis)

            # Step 6: Generate intelligent response
            response = self._generate_intelligent_response(
                message, context_analysis, historical_context, project_analysis
            )

            # Check for file operation request
            if response.startswith("FILE_EDIT_REQUEST:"):
                operation_result = self._process_file_edit_request(response, context_analysis)
                response = f"{response}\n\nOperation Result: {operation_result}"

            # Step 7: Update memory with response
            self._update_memory_with_response(response, context_analysis)

            # Step 8: Save memory periodically
            self.memory.last_activity = datetime.now()
            if len(self.memory.conversation_history) % 10 == 0:  # Save every 10 messages
                self.save_memory()

            # Add performance info
            response_time = time.time() - start_time
            enhanced_response = f"{response}\n\n_Response time: {response_time:.2f}s | Context confidence: {context_analysis.confidence_score:.2f}_"

            return enhanced_response

        except Exception as e:
            self.logger.error(f"Error in enhanced_chat: {str(e)}")
            return f"I encountered an error while processing your request: {str(e)}\n\nPlease ensure Ollama is running and try again."

    def _update_memory(self, message: str, analysis: ContextAnalysis):
        """Update memory with current message and analysis"""
        memory_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'intent': analysis.user_intent,
            'confidence': analysis.confidence_score,
            'mentioned_files': analysis.mentioned_files,
            'referenced_functions': analysis.referenced_functions,
            'code_patterns': analysis.code_patterns,
            'suggested_actions': analysis.suggested_actions
        }

        self.memory.conversation_history.append(memory_entry)

        # Keep memory manageable
        if len(self.memory.conversation_history) > 200:
            self.memory.conversation_history = self.memory.conversation_history[-200:]

    def _retrieve_relevant_context(self, message: str, analysis: ContextAnalysis) -> Dict[str, Any]:
        """Retrieve relevant historical context for the current message"""
        relevant_context = {
            'previous_messages': [],
            'related_file_operations': [],
            'learned_patterns': [],
            'project_insights': []
        }

        # Find similar previous messages
        message_lower = message.lower()
        for entry in reversed(self.memory.conversation_history[:-1]):  # Exclude current message
            entry_message = entry.get('message', '').lower()

            # Check for similar intent
            if entry.get('intent') == analysis.user_intent:
                relevant_context['previous_messages'].append(entry)
                if len(relevant_context['previous_messages']) >= 3:
                    break

            # Check for similar file mentions
            if any(file in entry_message for file in analysis.mentioned_files):
                relevant_context['previous_messages'].append(entry)

            # Check for similar function references
            if any(func in entry_message for func in analysis.referenced_functions):
                relevant_context['previous_messages'].append(entry)

        # Find related file operations
        for operation in reversed(self.memory.file_operations):
            if any(file in operation.get('file_path', '') for file in analysis.mentioned_files):
                relevant_context['related_file_operations'].append(operation)
                if len(relevant_context['related_file_operations']) >= 5:
                    break

        return relevant_context

    def _analyze_current_project_state(self, analysis: ContextAnalysis) -> Dict[str, Any]:
        """Analyze the current state of the project"""
        project_state = {
            'files_analyzed': 0,
            'total_files': 0,
            'languages': set(),
            'recent_changes': [],
            'project_health': 'unknown'
        }

        if analysis.mentioned_files:
            # Analyze mentioned files
            for file_path in analysis.mentioned_files:
                path = Path(file_path)
                if path.exists():
                    project_state['files_analyzed'] += 1
                    project_state['languages'].add(path.suffix)

                    # Get file info
                    try:
                        file_info = self.file_manager.get_file_info(path)
                        project_state['recent_changes'].append({
                            'file': str(path),
                            'modified': file_info['modified'],
                            'size': file_info['size']
                        })
                    except:
                        pass

        # Get total project files
        try:
            all_files = self.file_manager.get_project_files()
            project_state['total_files'] = len(all_files)
            project_state['languages'] = set(f.suffix for f in all_files if f.suffix)
        except:
            pass

        return project_state

    def _should_perform_file_operation(self, message: str, analysis: ContextAnalysis) -> bool:
        """Determine if the message requires file operations"""
        file_operation_keywords = [
            'create', 'make', 'new', 'add', 'edit', 'modify', 'change', 'update',
            'read', 'show', 'display', 'view', 'delete', 'remove', 'write', 'save'
        ]

        message_lower = message.lower()
        has_file_operation = any(keyword in message_lower for keyword in file_operation_keywords)
        has_file_mention = len(analysis.mentioned_files) > 0

        return has_file_operation or (has_file_mention and analysis.confidence_score > 0.7)

    def _handle_enhanced_file_operation(self, message: str, analysis: ContextAnalysis,
                                      historical_context: Dict[str, Any]) -> str:
        """Handle file operations with enhanced intelligence"""
        try:
            # Determine the primary file to work with
            target_file = None
            if analysis.mentioned_files:
                target_file = analysis.mentioned_files[0]
            elif self.memory.session_context.get('last_file'):
                target_file = self.memory.session_context['last_file']

            if not target_file:
                return "I need to know which file you'd like to work with. Please specify a filename."

            # Analyze the file if it exists
            file_analysis = None
            if Path(target_file).exists():
                file_analysis = self.code_analyzer.analyze_file(Path(target_file))

            # Determine operation type
            operation_type = self._determine_operation_type(message, analysis)

            # Execute the operation
            if operation_type == 'read':
                return self._enhanced_read_file(target_file, analysis, historical_context)
            elif operation_type == 'edit':
                return self._enhanced_edit_file(target_file, message, analysis, file_analysis)
            elif operation_type == 'create':
                return self._enhanced_create_file(target_file, message, analysis)
            elif operation_type == 'analyze':
                return self._enhanced_analyze_file(target_file, file_analysis)
            else:
                return f"I'm not sure what operation you want to perform on {target_file}. Could you clarify?"

        except Exception as e:
            return f"Error during file operation: {str(e)}"

    def _determine_operation_type(self, message: str, analysis: ContextAnalysis) -> str:
        """Determine the type of file operation requested"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['read', 'show', 'display', 'view', 'open']):
            return 'read'
        elif any(word in message_lower for word in ['edit', 'modify', 'change', 'update', 'fix']):
            return 'edit'
        elif any(word in message_lower for word in ['create', 'make', 'new', 'add']):
            return 'create'
        elif any(word in message_lower for word in ['analyze', 'review', 'check', 'examine']):
            return 'analyze'

        return 'unknown'

    def _enhanced_read_file(self, file_path: str, analysis: ContextAnalysis,
                           historical_context: Dict[str, Any]) -> str:
        """Enhanced file reading with context and analysis"""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"❌ File {file_path} does not exist."

            # Read file content
            content = self.file_manager.read_file(path)

            # Analyze the file
            file_analysis = self.code_analyzer.analyze_file(path)

            # Build enhanced response
            response_parts = [
                f"📖 **File: {file_path}**",
                f"**Size:** {len(content)} characters, {len(content.splitlines())} lines",
                f"**Language:** {file_analysis.language}",
                f"**Complexity:** {file_analysis.complexity_score}",
                ""
            ]

            # Add file summary
            if len(content) < 2000:  # Only show full content for smaller files
                response_parts.extend([
                    "**Content:**",
                    "```",
                    content,
                    "```",
                    ""
                ])
            else:
                # Show preview for large files
                lines = content.splitlines()
                preview = '\n'.join(lines[:20])
                response_parts.extend([
                    "**Content Preview (first 20 lines):**",
                    "```",
                    preview,
                    "..." if len(lines) > 20 else "",
                    "```",
                    ""
                ])

            # Add analysis insights
            if file_analysis.elements:
                functions = [e for e in file_analysis.elements if e.type == 'function']
                classes = [e for e in file_analysis.elements if e.type == 'class']

                response_parts.append("**Structure:**")
                if functions:
                    response_parts.append(f"- {len(functions)} functions: {', '.join(f.name for f in functions[:5])}")
                if classes:
                    response_parts.append(f"- {len(classes)} classes: {', '.join(c.name for c in classes[:5])}")
                response_parts.append("")

            # Add issues if any
            if file_analysis.issues:
                critical_issues = [i for i in file_analysis.issues if i.get('severity') == 'error']
                if critical_issues:
                    response_parts.extend([
                        "⚠️ **Critical Issues:**",
                        *[f"- {issue['message']}" for issue in critical_issues[:3]],
                        ""
                    ])

            # Add suggestions
            if file_analysis.suggestions:
                response_parts.extend([
                    "💡 **Suggestions:**",
                    *[f"- {suggestion}" for suggestion in file_analysis.suggestions[:3]],
                    ""
                ])

            # Record file operation in memory
            self._record_file_operation('read', file_path, {'size': len(content), 'lines': len(content.splitlines())})

            return '\n'.join(response_parts)

        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"

    def _enhanced_edit_file(self, file_path: str, message: str, analysis: ContextAnalysis,
                           file_analysis: Optional[FileAnalysis]) -> str:
        """Enhanced file editing with comprehensive analysis and safety"""
        try:
            path = Path(file_path)

            # Pre-edit analysis
            if path.exists():
                pre_analysis = self.analyze_before_edit(file_path, "User requested edit")
                if not pre_analysis["success"]:
                    return f"❌ Cannot edit {file_path}: {pre_analysis['error']}"

                # Show pre-edit warnings
                if pre_analysis.get("recommendations"):
                    warning_msg = "⚠️ **Pre-edit Analysis:**\n" + '\n'.join(f"- {rec}" for rec in pre_analysis["recommendations"][:3])
                    print(warning_msg)  # This would be shown to user in UI

            # Generate edit with enhanced context
            edit_result = self.smart_modify_file(file_path, message, backup=True)

            if edit_result["success"]:
                # Record successful operation
                self._record_file_operation('edit', file_path, {
                    'changes_summary': edit_result.get('changes_summary', ''),
                    'backup_created': edit_result.get('backup_created', False)
                })

                # Update session context
                self.memory.session_context['last_file'] = file_path

                response_parts = [
                    f"✅ **Successfully updated {file_path}**",
                    "",
                    "**Changes Summary:**",
                    edit_result.get('changes_summary', 'Minor modifications'),
                    ""
                ]

                # Add post-edit analysis
                if edit_result.get('post_analysis'):
                    post_analysis = edit_result['post_analysis']
                    if post_analysis.suggestions:
                        response_parts.extend([
                            "**Post-edit Suggestions:**",
                            *[f"- {s}" for s in post_analysis.suggestions[:3]],
                            ""
                        ])

                return '\n'.join(response_parts)
            else:
                return f"❌ Failed to edit {file_path}: {edit_result['error']}"

        except Exception as e:
            return f"Error editing file {file_path}: {str(e)}"

    def _enhanced_create_file(self, file_path: str, message: str, analysis: ContextAnalysis) -> str:
        """Enhanced file creation with intelligent content generation"""
        try:
            path = Path(file_path)

            # Check if file already exists
            if path.exists():
                return f"❌ File {file_path} already exists. Use edit operation instead."

            # Determine file type and generate content
            file_type = self._detect_file_type_from_path(file_path)
            content = self._generate_file_content(file_path, message, analysis, file_type)

            # Create the file
            self.file_manager.create_file(path, content)

            # Record operation
            self._record_file_operation('create', file_path, {
                'file_type': file_type,
                'size': len(content)
            })

            # Update session context
            self.memory.session_context['last_file'] = file_path

            return f"✅ **Created {file_path}**\n\n**Type:** {file_type}\n**Size:** {len(content)} characters\n\n**Content:**\n```\n{content}\n```"

        except Exception as e:
            return f"Error creating file {file_path}: {str(e)}"

    def _enhanced_analyze_file(self, file_path: str, file_analysis: Optional[FileAnalysis]) -> str:
        """Enhanced file analysis with comprehensive insights"""
        try:
            if not file_analysis:
                path = Path(file_path)
                if not path.exists():
                    return f"❌ File {file_path} does not exist."
                file_analysis = self.code_analyzer.analyze_file(path)

            response_parts = [
                f"🔍 **Analysis: {file_path}**",
                "",
                "**Overview:**",
                f"- Language: {file_analysis.language}",
                f"- Lines of code: {file_analysis.lines_of_code}",
                f"- Complexity score: {file_analysis.complexity_score}",
                f"- Total elements: {len(file_analysis.elements)}",
                ""
            ]

            # Structure analysis
            if file_analysis.elements:
                functions = [e for e in file_analysis.elements if e.type == 'function']
                classes = [e for e in file_analysis.elements if e.type == 'class']
                variables = [e for e in file_analysis.elements if e.type == 'variable']

                response_parts.append("**Code Structure:**")
                if functions:
                    response_parts.append(f"- Functions ({len(functions)}): {', '.join(f.name for f in functions[:5])}")
                if classes:
                    response_parts.append(f"- Classes ({len(classes)}): {', '.join(c.name for c in classes[:5])}")
                if variables:
                    response_parts.append(f"- Variables ({len(variables)}): {', '.join(v.name for v in variables[:5])}")
                response_parts.append("")

            # Dependencies
            if file_analysis.dependencies:
                response_parts.extend([
                    "**Dependencies:**",
                    f"- Imports: {', '.join(file_analysis.dependencies[:10])}",
                    ""
                ])

            # Issues and suggestions
            if file_analysis.issues:
                severity_counts = {}
                for issue in file_analysis.issues:
                    severity = issue.get('severity', 'info')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                response_parts.append("**Issues Found:**")
                for severity, count in severity_counts.items():
                    response_parts.append(f"- {severity.upper()}: {count} issues")
                response_parts.append("")

                # Show top issues
                top_issues = file_analysis.issues[:5]
                response_parts.append("**Top Issues:**")
                for issue in top_issues:
                    response_parts.append(f"- {issue.get('severity', 'info').upper()}: {issue.get('message', 'Unknown')}")
                response_parts.append("")

            if file_analysis.suggestions:
                response_parts.extend([
                    "**Improvement Suggestions:**",
                    *[f"- {suggestion}" for suggestion in file_analysis.suggestions[:5]],
                    ""
                ])

            return '\n'.join(response_parts)

        except Exception as e:
            return f"Error analyzing file {file_path}: {str(e)}"

    def _generate_file_content(self, file_path: str, message: str, analysis: ContextAnalysis, file_type: str) -> str:
        """Generate intelligent file content based on context"""
        # Extract content hints from message
        content_hints = []

        # Look for specific content requests
        if 'function' in message.lower():
            content_hints.append('function')
        if 'class' in message.lower():
            content_hints.append('class')
        if 'main' in message.lower():
            content_hints.append('main')

        # Generate content based on file type
        if file_type == 'python':
            return self._generate_python_content(file_path, content_hints, analysis)
        elif file_type in ['javascript', 'typescript']:
            return self._generate_js_content(file_path, content_hints, analysis)
        else:
            return self._generate_generic_content(file_path, file_type, content_hints)

    def _generate_python_content(self, file_path: str, content_hints: List[str], analysis: ContextAnalysis) -> str:
        """Generate Python file content"""
        filename = Path(file_path).stem

        content = [f'"""\n{filename}.py\nGenerated by DeepCode Enhanced Agent\n"""', ""]

        if 'main' in content_hints or not content_hints:
            content.extend([
                'def main():',
                '    """Main function"""',
                '    print("Hello from DeepCode!")',
                '    # Add your code here',
                '',
                '',
                'if __name__ == "__main__":',
                '    main()'
            ])
        elif 'function' in content_hints:
            content.extend([
                f'def {filename}_function():',
                '    """Sample function"""',
                '    return "Hello from function!"',
                '',
                '',
                f'# Usage: result = {filename}_function()'
            ])
        elif 'class' in content_hints:
            class_name = filename.title()
            content.extend([
                f'class {class_name}:',
                '    """Sample class"""',
                '    ',
                '    def __init__(self):',
                '        self.name = "DeepCode"',
                '    ',
                '    def greet(self):',
                '        return f"Hello from {self.name}!"'
            ])

        return '\n'.join(content)

    def _generate_js_content(self, file_path: str, content_hints: List[str], analysis: ContextAnalysis) -> str:
        """Generate JavaScript/TypeScript file content"""
        filename = Path(file_path).stem

        content = [f'// {filename}.js', '// Generated by DeepCode Enhanced Agent', '']

        if 'function' in content_hints or not content_hints:
            content.extend([
                'function main() {',
                '    console.log("Hello from DeepCode!");',
                '    // Add your code here',
                '}',
                '',
                'main();'
            ])
        elif 'class' in content_hints:
            class_name = filename.charAt(0).toUpperCase() + filename.slice(1)
            content.extend([
                f'class {class_name} {{',
                '    constructor() {',
                '        this.name = "DeepCode";',
                '    }',
                '    ',
                '    greet() {',
                '        return `Hello from ${this.name}!`;',
                '    }',
                '}',
                '',
                f'const instance = new {class_name}();',
                'console.log(instance.greet());'
            ])

        return '\n'.join(content)

    def _generate_generic_content(self, file_path: str, file_type: str, content_hints: List[str]) -> str:
        """Generate generic file content"""
        filename = Path(file_path).name
        return f'# {filename}\n# Generated by DeepCode Enhanced Agent\n# File type: {file_type}\n\n# Add your content here'

    def _detect_file_type_from_path(self, file_path: str) -> str:
        """Detect file type from file path"""
        extension = Path(file_path).suffix.lower()
        type_map = {
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
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
        return type_map.get(extension, 'text')

    def _record_file_operation(self, operation_type: str, file_path: str, details: Dict[str, Any]):
        """Record file operation in memory"""
        operation = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'file_path': file_path,
            'details': details
        }

        self.memory.file_operations.append(operation)

        # Keep operations manageable
        if len(self.memory.file_operations) > 100:
            self.memory.file_operations = self.memory.file_operations[-100:]

    def _generate_intelligent_response(self, message: str, analysis: ContextAnalysis,
                                     historical_context: Dict[str, Any],
                                     project_analysis: Dict[str, Any]) -> str:
        """Generate intelligent response using all available context"""
        # Build comprehensive context for AI
        context_parts = [
            "ENHANCED CONTEXT ANALYSIS:",
            f"User Intent: {analysis.user_intent} (confidence: {analysis.confidence_score:.2f})",
            f"Mentioned Files: {', '.join(analysis.mentioned_files) if analysis.mentioned_files else 'None'}",
            f"Referenced Functions: {', '.join(analysis.referenced_functions) if analysis.referenced_functions else 'None'}",
            f"Code Patterns: {', '.join(analysis.code_patterns) if analysis.code_patterns else 'None'}",
            ""
        ]

        # Add project context
        if project_analysis['total_files'] > 0:
            context_parts.extend([
                "PROJECT CONTEXT:",
                f"Total Files: {project_analysis['total_files']}",
                f"Languages: {', '.join(project_analysis['languages']) if project_analysis['languages'] else 'Unknown'}",
                f"Files Analyzed: {project_analysis['files_analyzed']}",
                ""
            ])

        # Add historical context
        if historical_context['previous_messages']:
            context_parts.append("RECENT CONVERSATION:")
            for prev_msg in historical_context['previous_messages'][-2:]:
                context_parts.append(f"- {prev_msg.get('message', '')[:100]}...")
            context_parts.append("")

        # Add learned patterns
        if self.memory.learned_patterns:
            context_parts.append("LEARNED PATTERNS:")
            for pattern, info in list(self.memory.learned_patterns.items())[:3]:
                context_parts.append(f"- {pattern}: {info}")
            context_parts.append("")

        # Create system prompt
        system_prompt = f"""You are DeepCode, a super-intelligent AI coding assistant with advanced memory and analysis capabilities.

        {chr(10).join(context_parts)}

        INSTRUCTIONS:
        - Use the enhanced context above to provide intelligent, context-aware responses
        - Reference previous conversations when relevant
        - Consider the user's intent and confidence score
        - Provide actionable suggestions based on the analysis
        - Be concise but comprehensive
        - If suggesting code changes, explain the reasoning
        - Remember what files the user has worked on recently

        ENHANCED FILE OPERATIONS:
        - CREATE: Create new files
        - READ: Read file contents
        - WRITE: Overwrite file contents (with backup)
        - APPEND: Add content to existing files
        - DELETE: Delete files (with confirmation and backup)
        - CLEAR: Clear file contents (with confirmation and backup)

        IMPORTANT: For file operations, respond with:
        FILE_EDIT_REQUEST: [filename] [action] [content]

        Where:
        - filename: the file to edit (use context if not specified)
        - action: READ, WRITE, APPEND, CREATE, DELETE, or CLEAR
        - content: the new content (for WRITE/CREATE/APPEND) or empty for DELETE/CLEAR

        Always consider the conversation history when determining which file the user is referring to. Be proactive in suggesting file operations when they would be helpful.

        Respond naturally and helpfully, leveraging all the context information provided."""

        # Build conversation messages
        messages = [ChatMessage("system", system_prompt)]

        # Add recent conversation history
        for entry in self.memory.conversation_history[-6:]:  # Last 3 exchanges
            if entry.get('message'):
                messages.append(ChatMessage("user", entry['message']))

        # Add current message
        messages.append(ChatMessage("user", message))

        # Generate response
        response = self.ollama.chat(messages, stream=False)

        return response

    def _update_memory_with_response(self, response: str, analysis: ContextAnalysis):
        """Update memory with AI response"""
        response_entry = {
            'timestamp': datetime.now().isoformat(),
            'response': response,
            'context_used': {
                'intent': analysis.user_intent,
                'confidence': analysis.confidence_score,
                'files_mentioned': analysis.mentioned_files
            }
        }

        # Add to conversation history
        self.memory.conversation_history[-1]['response'] = response_entry

    # Delegate methods to optimized agent for compatibility
    def _process_file_edit_request(self, response: str, analysis: ContextAnalysis) -> str:
        """Process file edit request from AI response"""
        try:
            # Parse the file edit request
            parts = response.split(':', 1)[1].strip().split(' ', 2)
            if len(parts) < 2:
                return "Invalid file edit request format"

            filename = parts[0].strip()
            action = parts[1].strip().upper()
            content = parts[2].strip() if len(parts) > 2 else ""

            file_path = Path(filename)

            if action == "READ":
                if file_path.exists():
                    content = self.file_manager.read_file(file_path)
                    return f"📖 Content of {filename}:\n\n{content}"
                else:
                    return f"❌ File {filename} does not exist"

            elif action in ["WRITE", "CREATE"]:
                if file_path.exists() and action == "WRITE":
                    self.file_manager.create_backup(file_path)

                self.file_manager.write_file(file_path, content)
                return f"✅ {'Created' if action == 'CREATE' else 'Updated'} {filename}"

            elif action == "APPEND":
                if file_path.exists():
                    existing_content = self.file_manager.read_file(file_path)
                    new_content = existing_content + "\n" + content
                    self.file_manager.create_backup(file_path)
                    self.file_manager.write_file(file_path, new_content)
                    return f"✅ Appended content to {filename}"
                else:
                    return f"❌ File {filename} does not exist for appending"

            elif action == "DELETE":
                result = self.file_manager.delete_file(file_path, force=False)
                if result["success"]:
                    return f"✅ Deleted {filename}"
                else:
                    return f"❌ Failed to delete {filename}: {result['error']}"

            elif action == "CLEAR":
                result = self.file_manager.clear_file(file_path, force=False)
                if result["success"]:
                    return f"✅ Cleared contents of {filename}"
                else:
                    return f"❌ Failed to clear {filename}: {result['error']}"

            else:
                return f"❌ Unknown action: {action}"

        except Exception as e:
            self.logger.error(f"Error processing file edit request: {str(e)}")
            return f"Error processing file edit request: {str(e)}"

    def analyze_before_edit(self, file_path: str, description: str):
        """Delegate to optimized agent method"""
        from .optimized_agent import OptimizedDeepCodeAgent
        temp_agent = OptimizedDeepCodeAgent(self.config)
        return temp_agent.analyze_before_edit(file_path, description)

    def smart_modify_file(self, file_path: str, description: str, backup: bool = True):
        """Delegate to optimized agent method"""
        from .optimized_agent import OptimizedDeepCodeAgent
        temp_agent = OptimizedDeepCodeAgent(self.config)
        return temp_agent.smart_modify_file(file_path, description, backup)

    def __del__(self):
        """Cleanup resources"""
        try:
            self.save_memory()
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except:
            pass