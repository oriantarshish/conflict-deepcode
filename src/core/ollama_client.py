"""
Ollama API Client for DeepCode
Handles communication with local Ollama instance
"""

import requests
import json
import time
from typing import Dict, List, Optional, Iterator, Any
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import threading

console = Console()

@dataclass
class ChatMessage:
    role: str
    content: str

class OllamaClient:
    def __init__(self, config):
        self.config = config
        self.host = config.get('ollama.host', 'http://localhost:11434')
        self.model = config.get('ollama.model', 'deepseek-coder-v2')
        # Optimized defaults for faster responses; can be overridden by CLI/config
        self.timeout = config.get('ollama.timeout', 15)  # Reduced to 15 seconds for faster responses
        self.num_ctx = config.get('ollama.num_ctx', config.get('ollama.max_tokens', 8192))  # Reduced context for speed
        self.num_predict = config.get('ollama.num_predict', 512)  # Reduced for faster generation
        self.temperature = config.get('ollama.temperature', 0.2)
        self.top_p = config.get('ollama.top_p', 0.9)
        self.fallback_timeout = config.get('ollama.fallback_timeout', 10)  # Fallback timeout reduced for speed
        
        # Performance monitoring
        self.response_times = []
        self.lock = threading.Lock()
        
    def is_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.host}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def has_model(self) -> bool:
        """Check if the required model is available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(self.model in model.get('name', '') for model in models)
            return False
        except:
            return False
    
    def pull_model(self) -> bool:
        """Pull the required model"""
        console.print(f"📥 Downloading {self.model}...")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Pulling {self.model}", total=None)
                
                response = requests.post(
                    f"{self.host}/api/pull",
                    json={"name": self.model},
                    stream=True,
                    timeout=300
                )
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'status' in data:
                                progress.update(task, description=data['status'])
                            if data.get('status') == 'success':
                                break
                        except json.JSONDecodeError:
                            continue
            
            console.print(f"✅ {self.model} downloaded successfully!")
            return True
            
        except Exception as e:
            console.print(f"❌ Failed to download model: {e}")
            return False
    
    def get_current_model(self) -> str:
        """Get currently configured model"""
        return self.model
    
    def chat(self, messages: List[ChatMessage], stream: bool = False, callback=None) -> str:
        """Send chat completion request with optional streaming callback"""
        payload = {
            "model": self.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": stream,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.num_predict,
                "repeat_penalty": 1.1
            }
        }
        
        # Try primary request with full timeout
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                # Even if stream=True is requested upstream, prefer non-streaming JSON parse on Windows
                # to prevent carriage-return/newline issues in certain terminals.
                try:
                    result_data = response.json()
                    result = result_data.get('message', {}).get('content', '')
                except Exception:
                    result = self._handle_streaming_response(response, callback)
            else:
                result_data = response.json()
                result = result_data.get('message', {}).get('content', '')
                
            # Track response time
            response_time = time.time() - start_time
            self._track_response_time(response_time)
            return result
                
        except requests.exceptions.Timeout:
            # Track timeout
            response_time = time.time() - start_time
            self._track_response_time(response_time, timed_out=True)
            
            # Try fallback with shorter timeout
            console.print("[yellow]⚠️  Request timed out, trying with shorter timeout...[/yellow]")
            fallback_start = time.time()
            try:
                response = requests.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=self.fallback_timeout,
                    stream=stream
                )
                response.raise_for_status()
                
                if stream:
                    result = self._handle_streaming_response(response, callback)
                else:
                    result_data = response.json()
                    result = result_data.get('message', {}).get('content', '')
                
                # Track fallback response time
                fallback_time = time.time() - fallback_start
                self._track_response_time(fallback_time)
                return result
            except requests.exceptions.Timeout:
                fallback_time = time.time() - fallback_start
                self._track_response_time(fallback_time, timed_out=True)
                raise Exception("Request timed out even with fallback timeout. Try simplifying your request or check if Ollama is responsive.")
            except requests.exceptions.RequestException as e:
                fallback_time = time.time() - fallback_start
                self._track_response_time(fallback_time, error=True)
                raise Exception(f"Fallback request failed: {e}")
        except requests.exceptions.RequestException as e:
            # Track error response time
            response_time = time.time() - start_time
            self._track_response_time(response_time, error=True)
            raise Exception(f"Request failed: {e}")
        except json.JSONDecodeError:
            # Track JSON error response time
            response_time = time.time() - start_time
            self._track_response_time(response_time, error=True)
            raise Exception("Invalid response from Ollama")
    
    def _handle_streaming_response(self, response, callback=None) -> str:
        """Handle streaming response from Ollama with optional callback"""
        full_response = ""
        
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'message' in data:
                            content = data['message'].get('content', '')
                            full_response += content
                            
                            # Use callback if provided, otherwise use console
                            if callback:
                                callback(content)
                            else:
                                console.print(content, end='', style="green")
                            
                        if data.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except requests.exceptions.ChunkedEncodingError:
            # Handle connection issues during streaming
            error_msg = "\n[yellow]⚠️  Connection interrupted during streaming[/yellow]"
            if callback:
                callback(error_msg)
            else:
                console.print(error_msg)
            full_response += error_msg
        except KeyboardInterrupt:
            if callback:
                callback("\n[yellow]⚠️  Generation interrupted[/yellow]")
            else:
                console.print("\n[yellow]⚠️  Generation interrupted[/yellow]")
            full_response += "\n⚠️  Generation interrupted"
            
        return full_response
    
    def generate_code(self, prompt: str, context: str = "", stream: bool = True) -> str:
        """Generate code with specific system prompt"""
        system_prompt = """You are DeepCode, an expert programming assistant. You help developers by:
1. Writing clean, efficient, and well-documented code
2. Following best practices and coding standards
3. Providing clear explanations for your solutions
4. Considering security and performance implications

When modifying code:
- Make minimal necessary changes
- Preserve existing functionality
- Add comments for complex logic
- Follow the existing code style

When creating new code:
- Use appropriate design patterns
- Include error handling
- Write readable and maintainable code
- Add docstrings and comments

Current context:
{context}

Please respond with code and brief explanation."""
        
        messages = [
            ChatMessage("system", system_prompt.format(context=context)),
            ChatMessage("user", prompt)
        ]
        
        return self.chat(messages, stream=stream)
    
    def explain_code(self, code: str, detail_level: str = "basic") -> str:
        """Explain code functionality"""
        detail_prompts = {
            "basic": "Provide a brief explanation of what this code does.",
            "detailed": "Provide a detailed explanation of this code, including its purpose, key components, and how it works.",
            "deep": "Provide a comprehensive analysis of this code, including purpose, algorithm, complexity, potential issues, and improvement suggestions."
        }
        
        prompt = f"""Please explain the following code:

{code}

{detail_prompts.get(detail_level, detail_prompts["basic"])}"""
        
        messages = [
            ChatMessage("system", "You are a code explanation expert. Provide clear, educational explanations."),
            ChatMessage("user", prompt)
        ]
        
        return self.chat(messages, stream=False)
    
    def review_code(self, code: str, review_type: str = "all") -> str:
        """Review code and provide suggestions"""
        review_prompts = {
            "security": "Focus on security vulnerabilities and potential exploits.",
            "performance": "Focus on performance optimization opportunities.",
            "maintainability": "Focus on code maintainability, readability, and structure.",
            "all": "Provide a comprehensive review covering security, performance, and maintainability."
        }
        
        prompt = f"""Please review the following code and provide suggestions:

{code}

Review focus: {review_prompts.get(review_type, review_prompts["all"])}

Please structure your review with:
1. Overall assessment
2. Specific issues found
3. Recommendations for improvement
4. Code examples where helpful"""
        
        messages = [
            ChatMessage("system", "You are a senior code reviewer with expertise in security, performance, and best practices."),
            ChatMessage("user", prompt)
        ]
        
        return self.chat(messages, stream=False)
    
    def generate_tests(self, code: str, framework: str = None) -> str:
        """Generate tests for given code"""
        framework_info = ""
        if framework:
            framework_info = f"Use {framework} testing framework."
        
        prompt = f"""Generate comprehensive tests for the following code:

{code}

Requirements:
- {framework_info}
- Include unit tests for all public functions/methods
- Test edge cases and error conditions
- Provide good test coverage
- Include setup and teardown if needed
- Add descriptive test names and comments

Please provide the complete test file."""
        
        messages = [
            ChatMessage("system", "You are a test automation expert. Generate thorough, well-structured tests."),
            ChatMessage("user", prompt)
        ]
        
        return self.chat(messages, stream=False)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model.get('name', '') for model in models]
            return []
        except:
            return []
    
    def _track_response_time(self, response_time: float, timed_out: bool = False, error: bool = False):
        """Track response time for performance monitoring"""
        with self.lock:
            self.response_times.append({
                'time': time.time(),
                'duration': response_time,
                'timed_out': timed_out,
                'error': error
            })
            
            # Keep only last 100 response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            if not self.response_times:
                return {
                    'total_requests': 0,
                    'average_response_time': 0,
                    'timeout_rate': 0,
                    'error_rate': 0
                }
            
            total_requests = len(self.response_times)
            successful_requests = [r for r in self.response_times if not r['timed_out'] and not r['error']]
            timeout_requests = [r for r in self.response_times if r['timed_out']]
            error_requests = [r for r in self.response_times if r['error']]
            
            avg_response_time = sum(r['duration'] for r in successful_requests) / len(successful_requests) if successful_requests else 0
            
            return {
                'total_requests': total_requests,
                'successful_requests': len(successful_requests),
                'timeout_requests': len(timeout_requests),
                'error_requests': len(error_requests),
                'average_response_time': round(avg_response_time, 2),
                'timeout_rate': round(len(timeout_requests) / total_requests * 100, 2),
                'error_rate': round(len(error_requests) / total_requests * 100, 2)
            }