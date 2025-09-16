"""
Core AI Agent for DeepCode
"""

import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .ollama_client import OllamaClient, ChatMessage
from .file_manager import FileManager
from .context_builder import ContextBuilder

@dataclass
class ConversationMemory:
    messages: list
    context: Dict[str, Any]
    timestamp: datetime
    task_type: str

class DeepCodeAgent:
    def __init__(self, config):
        self.config = config
        self.ollama = OllamaClient(config)
        self.file_manager = FileManager(config)
        self.context_builder = ContextBuilder(config)
        self.memory = []
        self.conversation_history = []  # Store conversation context
        self.current_context = {}  # Current working context
        self.last_file_mentioned = None  # Remember last file we worked on

    def create_file(self, target: str, file_type: str = None, template: str = None) -> Dict[str, Any]:
        """Create a new file or project structure"""
        try:
            if self.file_manager.is_directory_target(target):
                return self._create_project(target, file_type, template)
            else:
                return self._create_single_file(target, file_type, template)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_project(self, project_name: str, project_type: str, template: str) -> Dict[str, Any]:
        """Create a new project structure"""
        return {"success": True, "project": project_name, "files_created": []}

    def _create_single_file(self, filename: str, file_type: str, template: str) -> Dict[str, Any]:
        """Create a single file"""
        file_path = Path(filename)
        if not file_type:
            file_type = self._detect_file_type(file_path.suffix)
        
        content = f"# {filename}\n# Created by DeepCode\n"
        self.file_manager.create_file(file_path, content)
        
        return {
            "success": True,
            "file": str(file_path),
            "content": content,
            "explanation": f"Created {file_type} file"
        }

    def modify_file(self, file_path: str, description: str, backup: bool = True) -> Dict[str, Any]:
        """Modify an existing file based on description"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}
            
            if backup:
                self.file_manager.create_backup(file_obj)
            
            current_content = self.file_manager.read_file(file_obj)
            modified_content = current_content + f"\n# Modified: {description}\n"
            self.file_manager.write_file(file_obj, modified_content)
            
            return {
                "success": True,
                "file": str(file_obj),
                "original_size": len(current_content),
                "modified_size": len(modified_content),
                "backup_created": backup,
                "explanation": f"Modified file: {description}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def explain_file(self, file_path: str, detail_level: str = "basic") -> Dict[str, Any]:
        """Explain code in a file"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}
            
            content = self.file_manager.read_file(file_obj)
            explanation = f"This file contains {len(content.split())} words and {len(content.splitlines())} lines."
            
            return {
                "success": True,
                "file": str(file_obj),
                "explanation": explanation,
                "detail_level": detail_level
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def review_file(self, file_path: str, review_type: str = "all") -> Dict[str, Any]:
        """Review code in a file"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}
            
            content = self.file_manager.read_file(file_obj)
            review = f"File review: {len(content)} characters, {len(content.splitlines())} lines."
            
            return {
                "success": True,
                "file": str(file_obj),
                "review": review,
                "review_type": review_type
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_tests(self, file_path: str, framework: str = None) -> Dict[str, Any]:
        """Generate tests for a file"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}

            test_file_path = self._get_test_file_path(file_obj, framework)
            test_content = f"# Tests for {file_path}\n# Generated by DeepCode\n"
            self.file_manager.create_file(test_file_path, test_content)

            return {
                "success": True,
                "source_file": str(file_obj),
                "test_file": str(test_file_path),
                "framework": framework,
                "tests": test_content
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Delete a file with user confirmation for dangerous actions"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}

            # Check if this is a dangerous action that requires confirmation
            if not force and self._is_dangerous_file_operation(file_path, "delete"):
                confirmation = self._get_user_confirmation(
                    f"Are you sure you want to delete {file_path}? This action cannot be easily undone.",
                    f"File: {file_path}\nSize: {file_obj.stat().st_size} bytes\nModified: {file_obj.stat().st_mtime}"
                )
                if not confirmation:
                    return {"success": False, "error": "Operation cancelled by user"}

            result = self.file_manager.delete_file(file_obj, force)

            # Record in memory if successful
            if result["success"]:
                self._record_file_operation("delete", file_path, {
                    "backup_created": result.get("backup_created", False),
                    "size": file_obj.stat().st_size if file_obj.exists() else 0
                })

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def clear_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Clear file contents with user confirmation for dangerous actions"""
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {"success": False, "error": f"File {file_path} does not exist"}

            # Check if this is a dangerous action that requires confirmation
            if not force and self._is_dangerous_file_operation(file_path, "clear"):
                file_size = file_obj.stat().st_size
                confirmation = self._get_user_confirmation(
                    f"Are you sure you want to clear all contents of {file_path}? This will remove {file_size} bytes of data.",
                    f"File: {file_path}\nSize: {file_size} bytes\nLines: {len(self.file_manager.read_file(file_obj).splitlines())}"
                )
                if not confirmation:
                    return {"success": False, "error": "Operation cancelled by user"}

            result = self.file_manager.clear_file(file_obj, force)

            # Record in memory if successful
            if result["success"]:
                self._record_file_operation("clear", file_path, {
                    "backup_created": result.get("backup_created", False),
                    "original_size": file_obj.stat().st_size if file_obj.exists() else 0
                })

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_directory(self, dir_path: str, force: bool = False, recursive: bool = False) -> Dict[str, Any]:
        """Delete a directory with user confirmation for dangerous actions"""
        try:
            dir_obj = Path(dir_path)
            if not dir_obj.exists():
                return {"success": False, "error": f"Directory {dir_path} does not exist"}

            if not dir_obj.is_dir():
                return {"success": False, "error": f"{dir_path} is not a directory"}

            # Check if this is a dangerous action that requires confirmation
            if not force and self._is_dangerous_directory_operation(dir_path, recursive):
                item_count = len(list(dir_obj.rglob("*"))) if recursive else len(list(dir_obj.iterdir()))
                confirmation = self._get_user_confirmation(
                    f"Are you sure you want to delete directory {dir_path}?" + (" (recursive)" if recursive else ""),
                    f"Directory: {dir_path}\nItems: {item_count}\nRecursive: {recursive}"
                )
                if not confirmation:
                    return {"success": False, "error": "Operation cancelled by user"}

            result = self.file_manager.delete_directory(dir_obj, force, recursive)

            # Record in memory if successful
            if result["success"]:
                self._record_file_operation("delete_directory", dir_path, {
                    "recursive": recursive,
                    "item_count": len(result.get("manifest", []))
                })

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat(self, message: str, context: Dict[str, Any] = None) -> str:
        """Interactive chat mode with conversation memory and file editing capabilities"""
        try:
            # Update current context
            if context:
                self.current_context.update(context)
            
            # Add current message to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now()
            })
            
            # Extract and remember file mentions
            mentioned_file = self._extract_file_path(message, context)
            if mentioned_file:
                self.last_file_mentioned = mentioned_file
            
            # Build comprehensive context information
            context_info = self._build_context_info()
            
            # Check if this is a file editing request
            if self._should_edit_file(message) or self._is_continuation_of_file_work(message):
                return self.handle_file_edit_with_context(message, context)
            
            # Create enhanced system prompt with conversation memory
            system_prompt = f"""You are DeepCode, an expert AI coding assistant with advanced memory and file management capabilities. You help developers with:

1. **Code Generation**: Write clean, efficient, and well-documented code
2. **Code Explanation**: Explain how code works in simple terms
3. **Code Review**: Identify issues and suggest improvements
4. **Debugging**: Help find and fix bugs
5. **Best Practices**: Guide on coding standards and patterns
6. **Learning**: Teach programming concepts and techniques
7. **Advanced File Operations**: Create, read, modify, delete, and clear files
8. **Smart Context Awareness**: Remember previous conversations and file operations

IMPORTANT CONTEXT AND MEMORY:
{context_info}

CONVERSATION HISTORY (last 10 messages for better context):
{self._get_recent_conversation()}

RECENT FILE OPERATIONS:
{self._get_recent_file_operations()}

You have excellent memory of our conversation. If the user refers to "the file", "it", "that", or similar pronouns, use context from our conversation history and recent file operations to understand what they mean.

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

Always consider the conversation history when determining which file the user is referring to. Be proactive in suggesting file operations when they would be helpful."""
            
            # Build conversation messages with history
            messages = [ChatMessage("system", system_prompt)]
            
            # Add recent conversation history (last 6 exchanges for better context)
            recent_history = self.conversation_history[-12:]  # Last 6 user-assistant pairs
            for entry in recent_history:
                messages.append(ChatMessage(entry['role'], entry['content']))
            
            # Add current message
            messages.append(ChatMessage("user", message))
            
            # Get response from Ollama
            response = self.ollama.chat(messages, stream=False)
            
            # Add response to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            
            # Keep conversation history manageable (last 20 messages)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Check if response contains file edit request
            if response.startswith("FILE_EDIT_REQUEST:"):
                return self._process_file_edit_request(response, context)
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}\n\nPlease make sure Ollama is running and the model is available."

    def chat_streaming(self, message: str, context: Dict[str, Any] = None, typing_animation=None) -> str:
        """Interactive chat mode with streaming and typing animation"""
        try:
            # Update current context
            if context:
                self.current_context.update(context)
            
            # Add current message to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now()
            })
            
            # Extract and remember file mentions
            mentioned_file = self._extract_file_path(message, context)
            if mentioned_file:
                self.last_file_mentioned = mentioned_file
            
            # Build comprehensive context information
            context_info = self._build_context_info()
            
            # Check if this is a file editing request
            if self._should_edit_file(message) or self._is_continuation_of_file_work(message):
                return self.handle_file_edit_with_context(message, context)
            
            # Create enhanced system prompt with conversation memory
            system_prompt = f"""You are DeepCode, an expert AI coding assistant with advanced memory and file management capabilities. You help developers with:

1. **Code Generation**: Write clean, efficient, and well-documented code
2. **Code Explanation**: Explain how code works in simple terms
3. **Code Review**: Identify issues and suggest improvements
4. **Debugging**: Help find and fix bugs
5. **Best Practices**: Guide on coding standards and patterns
6. **Learning**: Teach programming concepts and techniques
7. **Advanced File Operations**: Create, read, modify, delete, and clear files
8. **Smart Context Awareness**: Remember previous conversations and file operations

IMPORTANT CONTEXT AND MEMORY:
{context_info}

CONVERSATION HISTORY (last 10 messages for better context):
{self._get_recent_conversation()}

RECENT FILE OPERATIONS:
{self._get_recent_file_operations()}

You have excellent memory of our conversation. If the user refers to "the file", "it", "that", or similar pronouns, use context from our conversation history and recent file operations to understand what they mean.

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

Always consider the conversation history when determining which file the user is referring to. Be proactive in suggesting file operations when they would be helpful."""
            
            # Build conversation messages with history
            messages = [ChatMessage("system", system_prompt)]
            
            # Add recent conversation history (last 6 exchanges for better context)
            recent_history = self.conversation_history[-12:]  # Last 6 user-assistant pairs
            for entry in recent_history:
                messages.append(ChatMessage(entry['role'], entry['content']))
            
            # Add current message
            messages.append(ChatMessage("user", message))
            
            # Create callback for streaming
            full_response = ""
            def streaming_callback(content):
                nonlocal full_response
                full_response += content
                if typing_animation:
                    typing_animation.add_text(content)
            
            # Get streaming response from Ollama
            response = self.ollama.chat(messages, stream=True, callback=streaming_callback)
            
            # Add response to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': full_response,
                'timestamp': datetime.now()
            })
            
            # Keep conversation history manageable (last 20 messages)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Check if response contains file edit request
            if full_response.startswith("FILE_EDIT_REQUEST:"):
                return self._process_file_edit_request(full_response, context)
            
            return full_response
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}\n\nPlease make sure Ollama is running and the model is available."

    def _detect_file_type(self, extension: str) -> str:
        """Detect file type from extension"""
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
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.vue': 'vue',
            '.jsx': 'jsx',
            '.tsx': 'tsx'
        }
        return type_map.get(extension.lower(), 'text')

    def _get_test_file_path(self, source_file: Path, framework: str = None) -> Path:
        """Generate appropriate test file path"""
        file_type = self._detect_file_type(source_file.suffix)
        if file_type == 'python':
            test_dir = source_file.parent / 'tests'
            test_dir.mkdir(exist_ok=True)
            return test_dir / f"test_{source_file.name}"
        elif file_type in ['javascript', 'typescript']:
            if framework == 'jest':
                return source_file.with_suffix('.test' + source_file.suffix)
            else:
                test_dir = source_file.parent / '__tests__'
                test_dir.mkdir(exist_ok=True)
                return test_dir / f"{source_file.stem}.test{source_file.suffix}"
        else:
            test_dir = source_file.parent / 'tests'
            test_dir.mkdir(exist_ok=True)
            return test_dir / f"test_{source_file.name}"

    def _build_context_info(self) -> str:
        """Build comprehensive context information"""
        context_parts = []
        
        # Current working directory
        if self.current_context.get('cwd'):
            context_parts.append(f"Current working directory: {self.current_context['cwd']}")
        
        # Available files
        if self.current_context.get('files'):
            context_parts.append(f"Available files: {', '.join(self.current_context['files'][:5])}")
        
        # Last file mentioned
        if self.last_file_mentioned:
            context_parts.append(f"Last file we worked on: {self.last_file_mentioned}")
        
        # Recent file operations
        recent_operations = self._get_recent_file_operations()
        if recent_operations:
            context_parts.append(f"Recent file operations: {recent_operations}")
        
        return "\n".join(context_parts) if context_parts else "No specific context available"

    def _get_recent_conversation(self) -> str:
        """Get recent conversation history for context"""
        if not self.conversation_history:
            return "No previous conversation"
        
        recent = self.conversation_history[-6:]  # Last 3 exchanges
        formatted = []
        
        for entry in recent:
            role = "User" if entry['role'] == 'user' else "Assistant"
            content = entry['content'][:100] + "..." if len(entry['content']) > 100 else entry['content']
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def _get_recent_file_operations(self) -> str:
        """Get recent file operations from memory"""
        if not hasattr(self, 'file_operations') or not self.file_operations:
            return "No recent file operations"

        operations = []
        for op in self.file_operations[-5:]:  # Last 5 operations
            operation = op['operation']
            file_path = op['file_path']
            timestamp = op['timestamp'][:19]  # YYYY-MM-DDTHH:MM:SS format

            if operation == 'delete':
                operations.append(f"Deleted {file_path} ({timestamp})")
            elif operation == 'clear':
                operations.append(f"Cleared {file_path} ({timestamp})")
            elif operation == 'create':
                operations.append(f"Created {file_path} ({timestamp})")
            elif operation == 'modify':
                operations.append(f"Modified {file_path} ({timestamp})")
            elif operation == 'delete_directory':
                operations.append(f"Deleted directory {file_path} ({timestamp})")

        return "\n".join(operations) if operations else "No recent file operations"

    def _is_continuation_of_file_work(self, message: str) -> bool:
        """Check if this message is a continuation of file work"""
        continuation_keywords = [
            'write', 'add', 'put', 'insert', 'create', 'make', 'build',
            'generate', 'code', 'function', 'class', 'method', 'script'
        ]
        
        message_lower = message.lower()
        has_continuation = any(keyword in message_lower for keyword in continuation_keywords)
        
        # If we have a last file mentioned and this looks like a continuation
        return has_continuation and self.last_file_mentioned is not None

    def _should_edit_file(self, message: str) -> bool:
        """Check if the message is requesting file editing"""
        edit_keywords = [
            'edit', 'modify', 'change', 'update', 'create', 'write', 'add to',
            'remove from', 'delete', 'replace', 'fix', 'correct', 'improve'
        ]
        file_keywords = ['file', 'code', 'script', 'function', 'class', 'method']
        
        message_lower = message.lower()
        has_edit = any(keyword in message_lower for keyword in edit_keywords)
        has_file = any(keyword in message_lower for keyword in file_keywords)
        
        return has_edit and has_file

    def handle_file_edit_with_context(self, message: str, context: Dict[str, Any] = None) -> str:
        """Handle file editing requests with conversation context"""
        try:
            # Determine which file to edit
            file_path = self._extract_file_path(message, context)
            
            # If no file specified, use the last file we worked on
            if not file_path and self.last_file_mentioned:
                file_path = self.last_file_mentioned
            
            if not file_path:
                return "I need to know which file you want to edit. Please specify the filename."
            
            # Read current file content
            current_content = ""
            if Path(file_path).exists():
                current_content = self.file_manager.read_file(Path(file_path))
            
            # Build context-aware prompt
            context_info = self._build_context_info()
            recent_conversation = self._get_recent_conversation()
            
            edit_prompt = f"""The user wants to edit the file: {file_path}

CONTEXT AND MEMORY:
{context_info}

RECENT CONVERSATION:
{recent_conversation}

Current file content:
```
{current_content}
```

User request: {message}

Based on our conversation history and the current file content, please provide the complete updated file content. If you're making changes, show the full file with your modifications. If you're adding content, include it in the appropriate place.

Respond with the complete file content wrapped in code blocks."""
            
            messages = [
                ChatMessage("system", "You are an expert code editor with memory of our conversation. Provide complete, working file content based on the context."),
                ChatMessage("user", edit_prompt)
            ]
            
            response = self.ollama.chat(messages, stream=False)
            
            # Extract code from response
            new_content = self._extract_code_from_response(response)
            if new_content:
                # Create backup
                if Path(file_path).exists():
                    self.file_manager.create_backup(Path(file_path))
                
                # Write new content
                self.file_manager.write_file(Path(file_path), new_content)
                
                # Update last file mentioned
                self.last_file_mentioned = file_path
                
                return f"✅ Successfully updated {file_path}\n\nChanges made:\n{self._get_changes_summary(current_content, new_content)}"
            else:
                return f"I couldn't extract valid code from my response. Here's what I generated:\n\n{response}"
                
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def _handle_file_edit(self, message: str, context: Dict[str, Any] = None) -> str:
        """Handle direct file editing requests (legacy method)"""
        return self.handle_file_edit_with_context(message, context)

    def _extract_file_path(self, message: str, context: Dict[str, Any] = None) -> str:
        """Extract file path from user message"""
        import re
        from pathlib import Path

        # Look for file extensions first
        file_patterns = [
            r'(\w+\.(py|js|ts|java|cpp|c|go|rs|php|rb|cs|swift|kt|scala|r|sql|html|css|scss|vue|jsx|tsx|json|yaml|yml|md|txt))',
            r'(\w+/\w+\.\w+)',
            r'(\w+\\\w+\.\w+)'  # Windows paths
        ]

        for pattern in file_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)

        # If no file found, check context files
        if context and context.get('files'):
            # Look for file mentions in the message
            for file_path in context['files']:
                filename = Path(file_path).name
                if filename.lower() in message.lower():
                    return file_path

        # Try to extract potential filename without extension
        # Look for words that could be filenames (preceded by "file", "in", etc.)
        filename_patterns = [
            r'(\w+)\s+file',  # "calculator file"
            r'file\s+(\w+)',  # "file calculator"
            r'in\s+the\s+(\w+)\s+file',  # "in the calculator file"
            r'(\w+)\s+(?:code|script|program)',  # "calculator code"
            r'(\w+)\s+(?:py|js|ts|java|cpp|c|go|rs|php|rb|cs|swift|kt|scala|r|sql|html|css|scss|vue|jsx|tsx|json|yaml|yml|md|txt)'  # "calculator py"
        ]

        potential_filenames = []
        for pattern in filename_patterns:
            matches = re.findall(pattern, message.lower())
            potential_filenames.extend(matches)

        # Remove duplicates and filter out common words
        common_words = {'the', 'a', 'an', 'new', 'in', 'for', 'to', 'with', 'of', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        potential_filenames = [name for name in potential_filenames if name not in common_words and len(name) > 2]

        # Choose the most relevant filename (longest one, or the one that appears most frequently)
        if potential_filenames:
            # Prefer longer names as they're more likely to be actual filenames
            potential_filename = max(potential_filenames, key=len)
        else:
            potential_filename = None

        if potential_filename:
            # Try common extensions in order of likelihood
            common_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt', '.scala', '.r', '.sql', '.html', '.css', '.scss', '.vue', '.jsx', '.tsx', '.json', '.yaml', '.yml', '.md', '.txt']

            # Check if file exists with any common extension
            for ext in common_extensions:
                candidate = potential_filename + ext
                if Path(candidate).exists():
                    return candidate

            # If no existing file found, assume .py for Python projects (most common)
            # Check if we're in a Python project by looking for .py files
            current_dir = Path('.')
            py_files = list(current_dir.glob('**/*.py'))
            if py_files:
                return potential_filename + '.py'

            # Otherwise, default to .py as it's the most common
            return potential_filename + '.py'

        return None

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code content from AI response"""
        import re
        
        # Look for code blocks
        code_patterns = [
            r'```(?:\w+)?\n(.*?)\n```',  # ```lang\ncode\n```
            r'```(.*?)```',  # ```code```
            r'`([^`]+)`'  # `code`
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                # Return the longest match (likely the main code)
                return max(matches, key=len).strip()
        
        # If no code blocks found, return the response as-is
        return response.strip()

    def _get_changes_summary(self, old_content: str, new_content: str) -> str:
        """Generate a summary of changes made"""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        if len(old_lines) != len(new_lines):
            return f"File length changed from {len(old_lines)} to {len(new_lines)} lines"
        
        changes = 0
        for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines)):
            if old_line != new_line:
                changes += 1
        
        if changes == 0:
            return "No changes detected"
        elif changes == 1:
            return "1 line modified"
        else:
            return f"{changes} lines modified"

    def _process_file_edit_request(self, response: str, context: Dict[str, Any] = None) -> str:
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
                    return f"📖 Content of {filename}:\n\n```\n{content}\n```"
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
                result = self.delete_file(filename, force=False)
                if result["success"]:
                    return f"✅ Deleted {filename}"
                else:
                    return f"❌ Failed to delete {filename}: {result['error']}"

            elif action == "CLEAR":
                result = self.clear_file(filename, force=False)
                if result["success"]:
                    return f"✅ Cleared contents of {filename}"
                else:
                    return f"❌ Failed to clear {filename}: {result['error']}"

            else:
                return f"❌ Unknown action: {action}"

        except Exception as e:
            return f"Error processing file edit request: {str(e)}"

    def _is_dangerous_file_operation(self, file_path: str, operation: str) -> bool:
        """Determine if a file operation is dangerous and requires confirmation"""
        file_obj = Path(file_path)

        # Always require confirmation for deletion
        if operation == "delete":
            return True

        # Require confirmation for clearing large files
        if operation == "clear":
            try:
                file_size = file_obj.stat().st_size
                return file_size > 1024  # 1KB threshold
            except:
                return True

        # Require confirmation for system files
        dangerous_patterns = [
            'package.json', 'requirements.txt', 'setup.py', 'Makefile',
            'Dockerfile', 'docker-compose.yml', '.env', 'config.json'
        ]

        filename = file_obj.name.lower()
        return any(pattern in filename for pattern in dangerous_patterns)

    def _is_dangerous_directory_operation(self, dir_path: str, recursive: bool) -> bool:
        """Determine if a directory operation is dangerous and requires confirmation"""
        dir_obj = Path(dir_path)

        # Always require confirmation for recursive deletion
        if recursive:
            return True

        # Require confirmation for non-empty directories
        try:
            items = list(dir_obj.iterdir())
            return len(items) > 0
        except:
            return True

    def _get_user_confirmation(self, message: str, details: str = None) -> bool:
        """Get user confirmation for dangerous operations"""
        # In a real implementation, this would show a dialog or prompt
        # For now, we'll simulate user interaction
        print(f"\n⚠️  DANGER: {message}")
        if details:
            print(f"Details: {details}")

        # For this implementation, we'll automatically confirm for testing
        # In production, this would wait for actual user input
        print("✅ Auto-confirmed for testing purposes")
        return True

    def _record_file_operation(self, operation: str, file_path: str, details: Dict[str, Any]):
        """Record file operation in memory for context"""
        if not hasattr(self, 'file_operations'):
            self.file_operations = []

        operation_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'file_path': file_path,
            'details': details
        }

        self.file_operations.append(operation_record)

        # Keep only recent operations
        if len(self.file_operations) > 20:
            self.file_operations = self.file_operations[-20:]
