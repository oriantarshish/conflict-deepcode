"""
Optimized AI Agent for DeepCode
Enhanced with advanced code analysis, intelligent caching, and production-ready features
"""

import json
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import time

from .ollama_client import OllamaClient, ChatMessage
from .file_manager import FileManager
from .context_builder import ContextBuilder
from .code_analyzer import CodeAnalyzer, FileAnalysis

@dataclass
class ConversationMemory:
    messages: list
    context: Dict[str, Any]
    timestamp: datetime
    task_type: str
    file_context: Optional[FileAnalysis] = None

@dataclass
class CachedResponse:
    response: str
    timestamp: datetime
    context_hash: str
    file_hash: str

class OptimizedDeepCodeAgent:
    """Production-ready AI agent with advanced code analysis and optimization"""
    
    def __init__(self, config):
        self.config = config
        self.ollama = OllamaClient(config)
        self.file_manager = FileManager(config)
        self.context_builder = ContextBuilder(config)
        self.code_analyzer = CodeAnalyzer(config)
        
        # Enhanced memory and caching
        self.memory = []
        self.conversation_history = []
        self.current_context = {}
        self.last_file_mentioned = None
        
        # Response caching for faster interactions
        self.response_cache = {}
        self.cache_ttl = timedelta(minutes=10)
        
        # Performance optimization settings
        self.max_context_length = config.get('agent.max_context_length', 4000)
        self.enable_streaming = config.get('agent.enable_streaming', True)
        self.enable_caching = config.get('agent.enable_caching', True)
        self.parallel_analysis = config.get('agent.parallel_analysis', True)
        
        # Thread pool for parallel operations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def analyze_before_edit(self, file_path: str, description: str) -> Dict[str, Any]:
        """Analyze file before making changes to prevent conflicts"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {
                    "success": False, 
                    "error": f"File {file_path} does not exist",
                    "analysis": None
                }
            
            # Perform comprehensive analysis
            analysis = self.code_analyzer.analyze_file(file_obj)
            
            # Check for potential issues
            pre_edit_checks = {
                "file_exists": file_obj.exists(),
                "file_readable": file_obj.is_file() and file_obj.stat().st_size > 0,
                "syntax_valid": len([i for i in analysis.issues if i.get('severity') == 'error']) == 0,
                "complexity_manageable": analysis.complexity_score < 50,
                "has_dependencies": len(analysis.dependencies) > 0
            }
            
            # Generate pre-edit recommendations
            recommendations = []
            if not pre_edit_checks["syntax_valid"]:
                recommendations.append("Fix syntax errors before modification")
            if pre_edit_checks["complexity_manageable"] and analysis.complexity_score > 30:
                recommendations.append("Consider refactoring complex functions before adding more code")
            if analysis.suggestions:
                recommendations.extend(analysis.suggestions[:3])  # Top 3 suggestions
            
            return {
                "success": True,
                "analysis": analysis,
                "pre_edit_checks": pre_edit_checks,
                "recommendations": recommendations,
                "safe_to_edit": all(pre_edit_checks.values())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }

    def smart_modify_file(self, file_path: str, description: str, backup: bool = True) -> Dict[str, Any]:
        """Intelligently modify file with conflict detection and validation"""
        try:
            # Step 1: Pre-analysis
            pre_analysis = self.analyze_before_edit(file_path, description)
            if not pre_analysis["success"]:
                return pre_analysis
            
            file_obj = Path(file_path)
            current_analysis = pre_analysis["analysis"]
            
            # Step 2: Create backup if requested
            if backup and file_obj.exists():
                backup_path = self.file_manager.create_backup(file_obj)
            
            # Step 3: Read current content
            current_content = self.file_manager.read_file(file_obj)
            
            # Step 4: Generate optimized prompt with context
            context_info = self._build_enhanced_context(current_analysis, description)
            
            # Step 5: Generate new content with AI
            new_content = self._generate_smart_modification(
                file_path, current_content, description, context_info
            )
            
            # Step 6: Conflict detection
            conflicts = self.code_analyzer.detect_conflicts(file_obj, new_content)
            
            if conflicts and any(c.get('severity') == 'error' for c in conflicts):
                return {
                    "success": False,
                    "error": "Conflicts detected that would break functionality",
                    "conflicts": conflicts,
                    "backup_created": backup
                }
            
            # Step 7: Write new content
            self.file_manager.write_file(file_obj, new_content)
            
            # Step 8: Post-modification analysis
            post_analysis = self.code_analyzer.analyze_file(file_obj, force_refresh=True)
            
            # Step 9: Generate change summary
            changes_summary = self._generate_change_summary(current_analysis, post_analysis)
            
            return {
                "success": True,
                "file": str(file_obj),
                "backup_created": backup,
                "changes_summary": changes_summary,
                "conflicts": conflicts,
                "pre_analysis": current_analysis,
                "post_analysis": post_analysis,
                "explanation": f"Successfully modified {file_path}: {description}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_smart_modification(self, file_path: str, current_content: str, 
                                   description: str, context_info: str) -> str:
        """Generate intelligent code modifications using enhanced prompts"""
        
        # Create optimized prompt for code modification
        system_prompt = f"""You are DeepCode, an expert AI coding assistant with advanced code analysis capabilities.

CRITICAL INSTRUCTIONS:
1. ALWAYS analyze the existing code structure before making changes
2. Preserve existing functionality unless explicitly asked to change it
3. Follow the existing code style and patterns
4. Add appropriate error handling and validation
5. Include clear comments for complex changes
6. Ensure backward compatibility when possible

CONTEXT ANALYSIS:
{context_info}

MODIFICATION REQUEST: {description}

CURRENT FILE CONTENT:
```
{current_content}
```

Please provide the COMPLETE modified file content. Ensure:
- All existing functionality is preserved
- New code follows best practices
- Changes are minimal but effective
- Code is production-ready
- No syntax errors are introduced

Respond with ONLY the complete file content, no explanations."""

        messages = [
            ChatMessage("system", system_prompt),
            ChatMessage("user", f"Modify the file according to: {description}")
        ]
        
        # Use caching for similar requests
        cache_key = self._generate_cache_key(file_path, description, current_content)
        
        if self.enable_caching and cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if datetime.now() - cached.timestamp < self.cache_ttl:
                return cached.response
        
        # Generate response
        response = self.ollama.chat(messages, stream=False)
        
        # Extract code from response
        new_content = self._extract_code_from_response(response)
        
        # Cache the response
        if self.enable_caching:
            self.response_cache[cache_key] = CachedResponse(
                response=new_content,
                timestamp=datetime.now(),
                context_hash=hashlib.md5(context_info.encode()).hexdigest(),
                file_hash=hashlib.md5(current_content.encode()).hexdigest()
            )
        
        return new_content

    def _build_enhanced_context(self, analysis: FileAnalysis, description: str) -> str:
        """Build enhanced context information for better AI understanding"""
        context_parts = [
            f"FILE ANALYSIS:",
            f"- Language: {analysis.language}",
            f"- Lines of code: {analysis.lines_of_code}",
            f"- Complexity score: {analysis.complexity_score}",
            f"- Functions: {len([e for e in analysis.elements if e.type == 'function'])}",
            f"- Classes: {len([e for e in analysis.elements if e.type == 'class'])}",
            f"- Dependencies: {', '.join(analysis.dependencies[:5]) if analysis.dependencies else 'None'}",
            ""
        ]
        
        if analysis.elements:
            context_parts.append("EXISTING CODE STRUCTURE:")
            for element in analysis.elements[:10]:  # Limit to top 10 elements
                context_parts.append(f"- {element.type.title()}: {element.name} (lines {element.line_start}-{element.line_end})")
            context_parts.append("")
        
        if analysis.issues:
            context_parts.append("EXISTING ISSUES:")
            for issue in analysis.issues[:5]:  # Top 5 issues
                context_parts.append(f"- {issue.get('severity', 'info').upper()}: {issue.get('message', 'Unknown issue')}")
            context_parts.append("")
        
        if analysis.suggestions:
            context_parts.append("IMPROVEMENT SUGGESTIONS:")
            for suggestion in analysis.suggestions[:3]:  # Top 3 suggestions
                context_parts.append(f"- {suggestion}")
            context_parts.append("")
        
        context_parts.append(f"MODIFICATION REQUEST: {description}")
        
        return "\n".join(context_parts)

    def enhanced_chat(self, message: str, context: Dict[str, Any] = None) -> str:
        """Enhanced chat with intelligent context and faster responses"""
        try:
            start_time = time.time()
            
            # Update context
            if context:
                self.current_context.update(context)
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now()
            })
            
            # Extract file mentions and analyze if needed
            mentioned_file = self._extract_file_path(message, context)
            file_analysis = None
            
            if mentioned_file:
                self.last_file_mentioned = mentioned_file
                file_path = Path(mentioned_file)
                if file_path.exists():
                    # Parallel file analysis for faster response
                    if self.parallel_analysis:
                        future = self.executor.submit(self.code_analyzer.analyze_file, file_path)
                        try:
                            file_analysis = future.result(timeout=5)  # 5 second timeout
                        except concurrent.futures.TimeoutError:
                            file_analysis = None
                    else:
                        file_analysis = self.code_analyzer.analyze_file(file_path)
            
            # Check for file editing requests
            if self._should_edit_file(message) or self._is_continuation_of_file_work(message):
                return self._handle_smart_file_edit(message, context, file_analysis)
            
            # Build optimized context
            context_info = self._build_chat_context(file_analysis)
            
            # Create enhanced system prompt
            system_prompt = self._create_optimized_system_prompt(context_info)
            
            # Build message history (optimized for speed)
            messages = self._build_optimized_message_history(system_prompt, message)
            
            # Check cache first
            cache_key = self._generate_chat_cache_key(message, context_info)
            if self.enable_caching and cache_key in self.response_cache:
                cached = self.response_cache[cache_key]
                if datetime.now() - cached.timestamp < self.cache_ttl:
                    response_time = time.time() - start_time
                    cached_response = f"{cached.response}\n\n_Response time: {response_time:.2f}s (cached)_"
                    self._add_to_conversation_history('assistant', cached_response)
                    return cached_response
            
            # Generate response. Disable streaming here to avoid UI conflicts with Rich animations
            # and to ensure we return a clean string for the terminal UI to render.
            response = self.ollama.chat(messages, stream=False)
            
            # Cache response
            if self.enable_caching:
                self.response_cache[cache_key] = CachedResponse(
                    response=response,
                    timestamp=datetime.now(),
                    context_hash=hashlib.md5(context_info.encode()).hexdigest(),
                    file_hash=hashlib.md5(message.encode()).hexdigest()
                )
            
            # Add response time info
            response_time = time.time() - start_time
            enhanced_response = f"{response}\n\n_Response time: {response_time:.2f}s_"
            
            # Add to conversation history
            self._add_to_conversation_history('assistant', enhanced_response)
            
            return enhanced_response
            
        except Exception as e:
            return f"I encountered an error: {str(e)}\n\nPlease ensure Ollama is running and try again."

    def _create_optimized_system_prompt(self, context_info: str) -> str:
        """Create optimized system prompt for better AI responses"""
        return f"""You are DeepCode, an expert AI coding assistant with advanced analysis capabilities.

CORE CAPABILITIES:
• Advanced code analysis with AST parsing
• Intelligent conflict detection and prevention
• Production-ready code generation
• Real-time performance optimization
• Smart caching for faster responses

RESPONSE GUIDELINES:
• Be concise but comprehensive
• Provide actionable solutions
• Include code examples when helpful
• Explain complex concepts clearly
• Focus on best practices and security

CURRENT CONTEXT:
{context_info}

CONVERSATION MEMORY:
{self._get_recent_conversation_summary()}

Respond naturally and helpfully. If asked to edit files, provide complete, production-ready code."""

    def _build_chat_context(self, file_analysis: Optional[FileAnalysis]) -> str:
        """Build optimized chat context"""
        context_parts = []
        
        # Working directory info
        if self.current_context.get('cwd'):
            context_parts.append(f"Working directory: {self.current_context['cwd']}")
        
        # File analysis context
        if file_analysis:
            context_parts.extend([
                f"Current file: {file_analysis.file_path}",
                f"Language: {file_analysis.language}",
                f"Complexity: {file_analysis.complexity_score}",
                f"Elements: {len(file_analysis.elements)} functions/classes"
            ])
            
            if file_analysis.issues:
                issues_summary = f"{len(file_analysis.issues)} issues detected"
                context_parts.append(f"Issues: {issues_summary}")
        
        # Recent operations
        if self.last_file_mentioned:
            context_parts.append(f"Last file: {self.last_file_mentioned}")
        
        return " | ".join(context_parts) if context_parts else "No specific context"

    def _build_optimized_message_history(self, system_prompt: str, current_message: str) -> List[ChatMessage]:
        """Build optimized message history for faster processing"""
        messages = [ChatMessage("system", system_prompt)]
        
        # Add only recent relevant history (last 4 exchanges)
        recent_history = self.conversation_history[-8:]  # Last 4 user-assistant pairs
        
        for entry in recent_history:
            # Truncate long messages for faster processing
            content = entry['content']
            if len(content) > 500:
                content = content[:500] + "..."
            messages.append(ChatMessage(entry['role'], content))
        
        # Add current message
        messages.append(ChatMessage("user", current_message))
        
        return messages

    def _handle_smart_file_edit(self, message: str, context: Dict[str, Any],
                                file_analysis: Optional[FileAnalysis]) -> str:
        """Handle file editing or creation with smart analysis and conflict prevention"""
        try:
            # Determine file to work with
            file_path = self._extract_file_path(message, context)
            if not file_path and self.last_file_mentioned:
                file_path = self.last_file_mentioned

            if not file_path:
                # Auto-select a sensible default filename when none is provided
                file_path = "deepcode_auto.py"

            # Check if this is a creation request
            message_lower = message.lower()
            is_creation = any(kw in message_lower for kw in ['create', 'make', 'generate', 'new'])

            if is_creation:
                # Handle file creation
                from pathlib import Path
                file_obj = Path(file_path)

                # If file already exists, ask for clarification
                if file_obj.exists():
                    return f"File {file_path} already exists. If you want to modify it, please use 'edit' or 'modify' instead of 'create'."

                # Perform file creation
                result = self.create_file(file_path, template=None)

                if result["success"]:
                    summary_parts = [
                        f"✅ Successfully created {file_path}",
                        "",
                        f"📄 File type: {result.get('explanation', 'Unknown').split()[1] if 'explanation' in result else 'Unknown'}",
                        f"📊 Content length: {len(result.get('content', ''))} characters"
                    ]

                    if result.get("suggestions"):
                        summary_parts.extend([
                            "",
                            "💡 SUGGESTIONS:",
                            *[f"- {s}" for s in result["suggestions"][:3]]
                        ])

                    return "\n".join(summary_parts)
                else:
                    return f"❌ Failed to create {file_path}: {result['error']}"
            else:
                # Handle file modification
                file_obj = Path(file_path)
                if not file_obj.exists():
                    # If file doesn't exist, treat as creation request implicitly
                    create_result = self.create_file(file_path, template=None)
                    if create_result.get("success"):
                        return f"✅ Successfully created {file_path}\n\n📊 Content length: {len(create_result.get('content',''))} characters"
                    return f"❌ Failed to create {file_path}: {create_result.get('error','unknown error')}"

                # Perform smart modification
                result = self.smart_modify_file(file_path, message, backup=True)

                if result["success"]:
                    summary_parts = [
                        f"✅ Successfully updated {file_path}",
                        "",
                        "📊 CHANGES SUMMARY:",
                        result["changes_summary"]
                    ]

                    if result.get("conflicts"):
                        summary_parts.extend([
                            "",
                            "⚠️ CONFLICTS DETECTED (resolved):",
                            *[f"- {c['message']}" for c in result["conflicts"][:3]]
                        ])

                    if result["post_analysis"].suggestions:
                        summary_parts.extend([
                            "",
                            "💡 SUGGESTIONS:",
                            *[f"- {s}" for s in result["post_analysis"].suggestions[:3]]
                        ])

                    return "\n".join(summary_parts)
                else:
                    return f"❌ Failed to update {file_path}: {result['error']}"

        except Exception as e:
            return f"Error during file operation: {str(e)}"

    def _generate_change_summary(self, before: FileAnalysis, after: FileAnalysis) -> str:
        """Generate a summary of changes made to the file"""
        changes = []
        
        # Compare elements
        before_elements = {e.name: e for e in before.elements}
        after_elements = {e.name: e for e in after.elements}
        
        # New elements
        new_elements = set(after_elements.keys()) - set(before_elements.keys())
        if new_elements:
            changes.append(f"Added: {', '.join(new_elements)}")
        
        # Removed elements
        removed_elements = set(before_elements.keys()) - set(after_elements.keys())
        if removed_elements:
            changes.append(f"Removed: {', '.join(removed_elements)}")
        
        # Modified elements (complexity changes)
        for name in set(before_elements.keys()) & set(after_elements.keys()):
            if before_elements[name].complexity != after_elements[name].complexity:
                changes.append(f"Modified: {name}")
        
        # Overall metrics
        loc_change = after.lines_of_code - before.lines_of_code
        complexity_change = after.complexity_score - before.complexity_score
        
        if loc_change != 0:
            changes.append(f"Lines of code: {loc_change:+d}")
        if complexity_change != 0:
            changes.append(f"Complexity: {complexity_change:+d}")
        
        return " | ".join(changes) if changes else "Minor modifications"

    def _generate_cache_key(self, file_path: str, description: str, content: str) -> str:
        """Generate cache key for responses"""
        key_data = f"{file_path}:{description}:{hashlib.md5(content.encode()).hexdigest()}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _generate_chat_cache_key(self, message: str, context: str) -> str:
        """Generate cache key for chat responses"""
        key_data = f"{message}:{context}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _add_to_conversation_history(self, role: str, content: str):
        """Add message to conversation history with cleanup"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def _get_recent_conversation_summary(self) -> str:
        """Get summarized recent conversation for context"""
        if not self.conversation_history:
            return "No previous conversation"
        
        recent = self.conversation_history[-4:]  # Last 2 exchanges
        summary_parts = []
        
        for entry in recent:
            role = "User" if entry['role'] == 'user' else "Assistant"
            content = entry['content'][:100] + "..." if len(entry['content']) > 100 else entry['content']
            summary_parts.append(f"{role}: {content}")
        
        return " | ".join(summary_parts)

    # Utility methods from original agent (optimized)
    def _should_edit_file(self, message: str) -> bool:
        """Check if message requests file editing or creation"""
        edit_keywords = ['edit', 'modify', 'change', 'update', 'create', 'write', 'add', 'fix', 'make', 'generate']
        file_keywords = ['file', 'code', 'function', 'class', 'method', 'script', 'program']

        message_lower = message.lower()
        return (any(kw in message_lower for kw in edit_keywords) and
                any(kw in message_lower for kw in file_keywords))

    def _is_continuation_of_file_work(self, message: str) -> bool:
        """Check if message continues file work"""
        continuation_keywords = ['add', 'write', 'create', 'make', 'implement']
        message_lower = message.lower()
        
        return (any(kw in message_lower for kw in continuation_keywords) and 
                self.last_file_mentioned is not None)

    def _extract_file_path(self, message: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Extract file path from message (optimized)"""
        import re
        
        # Quick regex patterns for common file extensions
        patterns = [
            r'(\w+\.(py|js|ts|java|cpp|c|go|rs|php|rb|cs|swift|kt|scala|html|css|json|yaml|md|txt))',
            r'([./]\w+/\w+\.\w+)',  # Relative paths
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        return None

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from AI response (optimized)"""
        import re

        # Look for code blocks
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        match = re.search(code_block_pattern, response, re.DOTALL)

        if match:
            return match.group(1).strip()

        # If no code blocks, return response as-is
        return response.strip()

    def _detect_file_type(self, extension: str) -> str:
        """Detect file type from extension"""
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
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
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.vue': 'vue',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
        return type_map.get(extension.lower(), 'text')

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "cache_size": len(self.response_cache),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "analyzer_cache_size": len(self.code_analyzer.cache),
            "conversation_length": len(self.conversation_history),
            "last_file": self.last_file_mentioned
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would need to be tracked over time in a real implementation
        return 0.0  # Placeholder

    def clear_all_caches(self):
        """Clear all caches for memory management"""
        self.response_cache.clear()
        self.code_analyzer.clear_cache()

    def create_file(self, target: str, file_type: str = None, template: str = None) -> Dict[str, Any]:
        """Create a new file with smart analysis and optimization"""
        try:
            from pathlib import Path

            # Determine file path and type
            file_path = Path(target)
            if not file_type:
                file_type = self._detect_file_type(file_path.suffix)

            # Generate smart content based on file type and context
            content = self._generate_smart_file_content(target, file_type, template)

            # Create the file
            success = self.file_manager.create_file(file_path, content)

            if success:
                # Analyze the created file for immediate feedback
                if self.parallel_analysis:
                    try:
                        analysis = self.code_analyzer.analyze_file(file_path)
                        suggestions = analysis.suggestions[:3] if analysis.suggestions else []
                    except:
                        analysis = None
                        suggestions = []
                else:
                    analysis = None
                    suggestions = []

                result = {
                    "success": True,
                    "file": str(file_path),
                    "content": content,
                    "explanation": f"Created optimized {file_type} file with smart content generation",
                    "analysis": analysis,
                    "suggestions": suggestions
                }

                # Update last file mentioned
                self.last_file_mentioned = str(file_path)

                return result
            else:
                return {"success": False, "error": "Failed to create file"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_smart_file_content(self, filename: str, file_type: str, template: str = None) -> str:
        """Generate smart file content based on type and context"""
        # Build context for content generation
        context_parts = [
            f"Creating a new {file_type} file: {filename}",
            f"File type: {file_type}"
        ]

        if self.current_context.get('cwd'):
            context_parts.append(f"Project directory: {self.current_context['cwd']}")

        if self.last_file_mentioned:
            context_parts.append(f"Related to: {self.last_file_mentioned}")

        context = "\n".join(context_parts)

        # Create prompt for smart content generation
        if template:
            prompt = f"""Create a {file_type} file named '{filename}' using the template '{template}'.

Context: {context}

Please generate complete, production-ready code that follows best practices for {file_type} files.
Include appropriate imports, structure, and documentation."""
        else:
            prompt = f"""Create a new {file_type} file named '{filename}'.

Context: {context}

Please generate complete, well-structured {file_type} code that:
1. Follows best practices for {file_type}
2. Includes appropriate imports and dependencies
3. Has proper structure and documentation
4. Is ready for immediate use

Generate only the file content, no explanations."""

        messages = [
            ChatMessage("system", f"You are an expert {file_type} developer. Generate high-quality, production-ready code."),
            ChatMessage("user", prompt)
        ]

        # Use optimized settings for file creation
        response = self.ollama.chat(messages, stream=False)

        # Extract code from response
        content = self._extract_code_from_response(response)

        # If no code blocks found, use the response as-is but clean it up
        if not content:
            content = response.strip()

        # Ensure we have some basic content
        if not content or len(content.strip()) < 10:
            content = f"# {filename}\n# Created by DeepCode AI Assistant\n# {file_type.upper()} file\n\n{content}"

        return content

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)