"""
Ollama API Client for DeepCode
Handles communication with local Ollama instance
"""

import requests
import json
import time
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        # Larger defaults for smarter, longer context; can be overridden by CLI/config
        self.timeout = config.get('ollama.timeout', 120)
        self.num_ctx = config.get('ollama.num_ctx', config.get('ollama.max_tokens', 32768))
        self.num_predict = config.get('ollama.num_predict', 2048)
        self.temperature = config.get('ollama.temperature', 0.2)
        self.top_p = config.get('ollama.top_p', 0.9)
        
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
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response, callback)
            else:
                result = response.json()
                return result.get('message', {}).get('content', '')
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Try increasing the timeout in config.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except json.JSONDecodeError:
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
                        
        except KeyboardInterrupt:
            if callback:
                callback("\n[yellow]⚠️  Generation interrupted[/yellow]")
            else:
                console.print("\n[yellow]⚠️  Generation interrupted[/yellow]")
            
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