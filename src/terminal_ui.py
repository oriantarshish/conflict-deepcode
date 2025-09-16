#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversational Terminal UI for Conflict DeepCode
Creates an immersive, chatbot-like terminal experience.
"""

import os
import sys
import time
import threading
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table
from rich import box
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.live import Live
from rich.layout import Layout
import click
from typing import Dict, Any
import re
import difflib

# Import our existing modules
from core.agent import DeepCodeAgent
from core.optimized_agent import OptimizedDeepCodeAgent
from core.ollama_client import OllamaClient
from utils.config import Config

COMMANDS = {
    "/help": "Show available commands",
    "/menu": "Show main menu",
    "/create": "Create new files or projects",
    "/modify": "Modify existing code",
    "/explain": "Explain code functionality",
    "/review": "Review code quality",
    "/test": "Generate tests",
    "/status": "Show project status",
    "/init": "Initialize project",
    "/typing": "Toggle typing animation on/off",
    "/optimize": "Toggle optimized agent mode",
    "/stats": "Show performance statistics",
    "/cache": "Clear all caches",
    "/analyze": "Analyze current file",
    "/exit": "Exit Conflict DeepCode",
    "/quit": "Exit Conflict DeepCode",
    "/back": "Return to main menu",
}

class TypingAnimation:
    """Handles typing animation for AI responses"""
    
    def __init__(self, console):
        self.console = console
        self.current_text = ""
        self.is_typing = False
        self.typing_speed = 0.01  # Faster typing speed
        
    def start_typing(self, text=""):
        """Start the typing animation"""
        self.current_text = text
        self.is_typing = True
        
    def add_text(self, text):
        """Add text to the current response"""
        self.current_text += text
        
    def stop_typing(self):
        """Stop the typing animation"""
        self.is_typing = False
        
    def display_typing_response(self, full_response):
        """Display response with typing animation using Rich Live"""
        self.console.print()

        # Create a panel for the response
        panel = Panel(
            "",
            title="[bold cyan]🤖 DeepCode[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )

        # Use Rich Live for smooth in-place updates
        with Live(panel, console=self.console, refresh_per_second=20) as live:
            displayed_text = ""
            for char in full_response:
                displayed_text += char
                panel.renderable = Markdown(displayed_text)
                live.update(panel)

                # Adjust speed based on character type
                if char in ".,!?;:":
                    time.sleep(self.typing_speed * 3)  # Pause for punctuation
                elif char == " ":
                    time.sleep(self.typing_speed * 0.5)  # Faster for spaces
                else:
                    time.sleep(self.typing_speed)

        self.console.print()  # Add newline after response

class ConflictDeepCodeUI:
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.agent = None
        self.ollama = None
        self.typing_animation = TypingAnimation(self.console)
        self.enable_typing_animation = True  # Can be configured
        self.use_optimized_agent = True  # Use optimized agent by default
        self.current_file = None  # Track current file being worked on

    def show_banner(self):
        """Display the minimal Conflict DeepCode banner with ASCII art"""
        banner = """
                                                                              
                                                                              
         █████╗  █████╗ ███╗  ██╗███████╗██╗     ██╗  █████╗ ████████╗        
        ██╔══██╗██╔══██╗████╗ ██║██╔════╝██║     ██║ ██╔══██╗╚══██╔══╝        
        ██║  ╚═╝██║  ██║██╔██╗██║█████╗  ██║     ██║ ██║  ╚═╝   ██║           
        ██║  ██╗██║  ██║██║╚████║██╔══╝  ██║     ██║ ██║  ██╗   ██║           
        ╚█████╔╝╚█████╔╝██║ ╚███║██║     ███████╗██║ ╚█████╔╝   ██║           
         ╚════╝  ╚════╝ ╚═╝  ╚══╝╚═╝     ╚══════╝╚═╝  ╚════╝    ╚═╝           
                                                                              
                                                                              
        """

        panel = Panel(
            Align.center(Text(banner, style="bold cyan")),
            title="[bold white]Welcome to Conflict DeepCode[/bold white]",
            subtitle="[dim]Your AI coding companion is ready to help[/dim]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def show_loading_animation(self, message="Initializing..."):
        """Show a beautiful loading animation"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(message, total=None)
            time.sleep(2)  # Simulate loading time

    def check_ollama_connection(self):
        """Check and display Ollama connection status"""
        self.console.print("🔍 [bold]Checking Ollama connection...[/bold]")

        try:
            self.ollama = OllamaClient(self.config)

            if not self.ollama.is_available():
                self.console.print("❌ [red]Ollama is not running or not accessible[/red]")
                self.show_ollama_setup_guide()
                return False

            if not self.ollama.has_model():
                self.console.print("⚠️  [yellow]DeepSeek Coder V2 model not found[/yellow]")
                if Confirm.ask("Do you want to download it now?"):
                    self.download_model()
                else:
                    self.console.print("❌ [red]Model required to continue[/red]")
                    return False

            self.console.print("✅ [green]Ollama connected successfully[/green]")
            self.console.print(f"🤖 [cyan]Model: {self.ollama.get_current_model()}[/cyan]")
            return True

        except Exception as e:
            self.console.print(f"❌ [red]Connection error: {e}[/red]")
            return False

    def show_ollama_setup_guide(self):
        """Show Ollama setup instructions"""
        setup_guide = """
[bold yellow]Ollama Setup Required[/bold yellow]

1. [bold]Install Ollama:[/bold] Visit https://ollama.ai and download for your OS
2. [bold]Start Ollama:[/bold] Run `ollama serve` in your terminal
3. [bold]Pull Model:[/bold] Run `ollama pull deepseek-coder-v2`
4. [bold]Restart:[/bold] Run `deepcode` again

[dim]Ollama provides the AI model that powers Conflict DeepCode[/dim]
        """

        panel = Panel(
            Markdown(setup_guide),
            title="[bold red]Setup Required[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )
        self.console.print(panel)

    def download_model(self):
        """Download the DeepSeek model with progress"""
        self.console.print("📥 [bold]Downloading DeepSeek Coder V2 model...[/bold]")
        self.console.print("[dim]This may take a few minutes depending on your internet connection[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Downloading model...", total=None)
            self.ollama.pull_model()

        self.console.print("✅ [green]Model downloaded successfully![/green]")

    def show_help(self):
        """Show available commands in a nice panel"""
        help_md = "\n".join(
            f"- [bold cyan]{cmd}[/bold cyan]: {desc}" for cmd, desc in COMMANDS.items()
        )
        panel = Panel(
            Markdown(f"**Available Commands:**\n\n{help_md}"),
            title="[bold magenta]Help[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)

    def show_main_menu(self):
        """Display the main menu as a table (for /menu command)"""
        table = Table(title="[bold cyan]Conflict DeepCode - Main Menu[/bold cyan]", box=box.ROUNDED)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        for cmd, desc in COMMANDS.items():
            if cmd in ["/exit", "/quit", "/back"]:  # Only show /exit once
                continue
            table.add_row(cmd, desc)
        self.console.print(table)
        self.console.print("[dim]Type a command (e.g. /create) or just chat with the AI.[/dim]")

    def start_interactive_session(self):
        """Start the conversational chatbot-like session"""
        self.show_banner()

        # Check Ollama connection
        if not self.check_ollama_connection():
            return

        # Initialize agent (optimized by default)
        if self.use_optimized_agent:
            self.agent = OptimizedDeepCodeAgent(self.config)
            agent_type = "Optimized"
        else:
            self.agent = DeepCodeAgent(self.config)
            agent_type = "Legacy"

        features_text = "[dim]Ask me anything about coding! I can help you with:\n"
        if self.use_optimized_agent:
            features_text += "• 🚀 Advanced code analysis with AST parsing\n"
            features_text += "• ⚡ Smart caching for faster responses\n"
            features_text += "• 🛡️ Intelligent conflict detection\n"
            features_text += "• 🎯 Production-ready code generation\n"
        else:
            features_text += "• Generate code and explain concepts\n"
            features_text += "• Review and improve your code\n"
            features_text += "• Answer programming questions\n"
            features_text += "• Create projects and files\n"
        
        features_text += f"\nType /help for commands or just start chatting! Type /exit to quit.[/dim]"
        
        self.console.print(
            Panel(
                f"[bold green]🤖 dpcd Chatbox Active ({agent_type} Mode)[/bold green]\n" + features_text,
                title="[bold cyan]dpcd - Your AI Coding Assistant[/bold cyan]",
                border_style="green",
                box=box.ROUNDED
            )
        )

        while True:
            try:
                user_input = self.console.input("[bold green]💬 You:[/bold green] ").strip()
                if not user_input:
                    continue

                # Command handling
                if user_input.startswith("/"):
                    cmd, *args = user_input.split()
                    cmd = cmd.lower()
                    if cmd in ("/exit", "/quit"):
                        self.show_goodbye()
                        break
                    elif cmd == "/help":
                        self.show_help()
                    elif cmd == "/menu":
                        self.show_main_menu()
                    elif cmd == "/create":
                        self.create_mode(args)
                    elif cmd == "/modify":
                        self.modify_mode(args)
                    elif cmd == "/explain":
                        self.explain_mode(args)
                    elif cmd == "/review":
                        self.review_mode(args)
                    elif cmd == "/test":
                        self.test_mode(args)
                    elif cmd == "/status":
                        self.status_mode()
                    elif cmd == "/init":
                        self.init_mode()
                    elif cmd == "/typing":
                        self.toggle_typing_animation()
                    elif cmd == "/optimize":
                        self.toggle_optimized_mode()
                    elif cmd == "/stats":
                        self.show_performance_stats()
                    elif cmd == "/cache":
                        self.clear_caches()
                    elif cmd == "/analyze":
                        self.analyze_current_file(args)
                    elif cmd == "/cd":
                        if args:
                            try:
                                os.chdir(" ".join(args))
                                self.console.print(f"📂 Changed directory to {os.getcwd()}")
                            except Exception as e:
                                self.console.print(f"[red]Failed to change directory: {e}[/red]")
                        else:
                            self.console.print("[yellow]Please provide a path, e.g. /cd path/to/dir[/yellow]")
                    elif cmd == "/back":
                        self.console.print("[dim]Already at main chat. Type /exit to quit.[/dim]")
                    else:
                        self.console.print(f"[red]Unknown command:[/red] {cmd}. Type /help.")
                    continue

                # Check if this is a coding/fixing request
                if self._is_coding_request(user_input):
                    self._handle_coding_request(user_input)
                    continue

                # Otherwise, treat as regular chat
                context = self.get_current_context()

                # Show thinking indicator
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task("🤖 DeepCode is thinking...", total=None)

                    # Get response based on agent type
                    if self.use_optimized_agent:
                        response = self.agent.enhanced_chat(user_input, context)
                    else:
                        response = self.agent.chat_streaming(user_input, context, self.typing_animation)

                # Display the response with or without typing animation
                if response and not response.startswith("FILE_EDIT_REQUEST:"):
                    if self.enable_typing_animation:
                        self.typing_animation.display_typing_response(response)
                    else:
                        # Display without animation
                        response_panel = Panel(
                            Markdown(response),
                            title="[bold cyan]🤖 DeepCode[/bold cyan]",
                            border_style="cyan",
                            box=box.ROUNDED,
                            padding=(1, 2)
                        )
                        self.console.print(response_panel)
                        self.console.print()

            except KeyboardInterrupt:
                self.show_goodbye()
                break
            except Exception as e:
                self.console.print(f"❌ [red]Error: {e}[/red]")

    def create_mode(self, args=None):
        """Create mode interface (conversational)"""
        self.console.print()
        if args and len(args) >= 1:
            target = " ".join(args)
        else:
            target = self.console.input("[bold cyan]📝 What would you like to create?[/bold cyan] ").strip()
        project_type = self.console.input("[bold cyan]Project type (default: python):[/bold cyan] ").strip() or "python"

        from commands.create import create_handler
        ctx = type('Context', (), {
            'obj': {
                'config': self.config,
                'console': self.console
            }
        })()
        create_handler(ctx, target, project_type, None)

    def modify_mode(self, args=None):
        """Modify mode interface (conversational)"""
        self.console.print()
        if args and len(args) >= 2:
            file_path = args[0]
            description = " ".join(args[1:])
        else:
            file_path = self.console.input("[bold cyan]✏️  File to modify:[/bold cyan] ").strip()
            description = self.console.input("[bold cyan]What changes do you want to make?[/bold cyan] ").strip()

        from commands.modify import modify_handler
        ctx = type('Context', (), {
            'obj': {
                'config': self.config,
                'console': self.console
            }
        })()
        modify_handler(ctx, file_path, description, True)

    def explain_mode(self, args=None):
        """Explain mode interface (conversational)"""
        self.console.print()
        if args and len(args) >= 1:
            file_path = args[0]
        else:
            file_path = self.console.input("[bold cyan]📖 File to explain:[/bold cyan] ").strip()
        detail = self.console.input("[bold cyan]Detail level (basic/detailed/deep, default: basic):[/bold cyan] ").strip() or "basic"

        from commands.explain import explain_handler
        ctx = type('Context', (), {
            'obj': {
                'config': self.config,
                'console': self.console
            }
        })()
        explain_handler(ctx, file_path, detail)

    def review_mode(self, args=None):
        """Review mode interface (conversational)"""
        self.console.print()
        if args and len(args) >= 1:
            file_path = args[0]
        else:
            file_path = self.console.input("[bold cyan]🔍 File to review:[/bold cyan] ").strip()
        style = self.console.input("[bold cyan]Review style (security/performance/maintainability/all, default: all):[/bold cyan] ").strip() or "all"

        from commands.review import review_handler
        ctx = type('Context', (), {
            'obj': {
                'config': self.config,
                'console': self.console
            }
        })()
        review_handler(ctx, file_path, style)

    def test_mode(self, args=None):
        """Test mode interface (conversational)"""
        self.console.print()
        if args and len(args) >= 1:
            file_path = args[0]
        else:
            file_path = self.console.input("[bold cyan]🧪 File to generate tests for:[/bold cyan] ").strip()
        framework = self.console.input("[bold cyan]Testing framework (default: pytest):[/bold cyan] ").strip() or "pytest"

        from commands.test import test_handler
        ctx = type('Context', (), {
            'obj': {
                'config': self.config,
                'console': self.console
            }
        })()
        test_handler(ctx, file_path, framework, False)

    def status_mode(self):
        """Status mode interface"""
        self.console.print()
        table = Table(title="[bold cyan]📊 Project Status[/bold cyan]", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        if self.ollama and self.ollama.is_available():
            table.add_row("Ollama", "✅ Connected", self.ollama.get_current_model())
        else:
            table.add_row("Ollama", "❌ Disconnected", "Not available")

        if Path('.deepcode').exists():
            table.add_row("Project", "✅ Initialized", "DeepCode config found")
        else:
            table.add_row("Project", "⚠️  Not initialized", "Run '/init'")

        current_dir = Path('.')
        py_files = len(list(current_dir.glob('**/*.py')))
        js_files = len(list(current_dir.glob('**/*.js')))
        total_files = len([f for f in current_dir.rglob('*') if f.is_file()])

        table.add_row("Files", f"📁 {total_files} total", f"{py_files} Python, {js_files} JavaScript")
        self.console.print(table)

    def init_mode(self):
        """Init mode interface"""
        self.console.print()
        self.console.print("🚀 [bold]Initializing DeepCode in current directory...[/bold]")

        deepcode_dir = Path('.deepcode')
        deepcode_dir.mkdir(exist_ok=True)

        local_config = deepcode_dir / 'config.yaml'
        if not local_config.exists():
            with open(local_config, 'w') as f:
                f.write("""# DeepCode local configuration
project:
  name: ""
  description: ""
  language: ""

ignore_patterns:
  - ".git"
  - "node_modules"
  - "__pycache__"
  - "*.pyc"
  - ".deepcode"
""")

        gitignore = Path('.gitignore')
        gitignore_content = ""
        if gitignore.exists():
            gitignore_content = gitignore.read_text()

        if '.deepcode/' not in gitignore_content:
            with open(gitignore, 'a') as f:
                f.write('\n# DeepCode\n.deepcode/\n')

        self.console.print("✅ [green]DeepCode initialized successfully![/green]")
        self.console.print(f"📁 [cyan]Config: {local_config}[/cyan]")

    def toggle_typing_animation(self):
        """Toggle typing animation on/off"""
        self.enable_typing_animation = not self.enable_typing_animation
        status = "enabled" if self.enable_typing_animation else "disabled"
        self.console.print(f"⌨️  [cyan]Typing animation {status}[/cyan]")

    def toggle_optimized_mode(self):
        """Toggle between optimized and legacy agent"""
        self.use_optimized_agent = not self.use_optimized_agent
        
        # Reinitialize agent
        if self.use_optimized_agent:
            self.agent = OptimizedDeepCodeAgent(self.config)
            mode = "Optimized"
            features = "Advanced analysis, smart caching, conflict detection enabled"
        else:
            self.agent = DeepCodeAgent(self.config)
            mode = "Legacy"
            features = "Basic functionality"
        
        self.console.print(f"🔄 [cyan]Switched to {mode} mode[/cyan]")
        self.console.print(f"[dim]{features}[/dim]")

    def show_performance_stats(self):
        """Show performance statistics for optimized agent"""
        if not self.use_optimized_agent:
            self.console.print("[yellow]Performance stats only available in optimized mode[/yellow]")
            return
        
        try:
            stats = self.agent.get_performance_stats()
            analyzer_stats = self.agent.code_analyzer.get_cache_stats()
            
            table = Table(title="[bold cyan]📊 Performance Statistics[/bold cyan]", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Details", style="white")
            
            table.add_row("Response Cache", str(stats['cache_size']), "Cached responses for faster replies")
            table.add_row("Analyzer Cache", str(stats['analyzer_cache_size']), "Analyzed files in memory")
            table.add_row("Conversation Length", str(stats['conversation_length']), "Messages in current session")
            table.add_row("Current File", stats['last_file'] or "None", "Last file worked on")
            table.add_row("Memory Usage", f"{analyzer_stats['memory_usage']} bytes", "Cache memory footprint")
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error getting stats: {e}[/red]")

    def clear_caches(self):
        """Clear all caches"""
        if not self.use_optimized_agent:
            self.console.print("[yellow]Cache clearing only available in optimized mode[/yellow]")
            return
        
        try:
            self.agent.clear_all_caches()
            self.console.print("🧹 [green]All caches cleared successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]Error clearing caches: {e}[/red]")

    def analyze_current_file(self, args=None):
        """Analyze the current file or specified file"""
        if not self.use_optimized_agent:
            self.console.print("[yellow]File analysis only available in optimized mode[/yellow]")
            return
        
        # Determine file to analyze
        if args and len(args) > 0:
            file_path = args[0]
        elif self.current_file:
            file_path = self.current_file
        else:
            file_path = self.console.input("[bold cyan]📁 File to analyze:[/bold cyan] ").strip()
        
        if not file_path:
            self.console.print("[red]No file specified[/red]")
            return
        
        try:
            from pathlib import Path
            file_obj = Path(file_path)
            
            if not file_obj.exists():
                self.console.print(f"[red]File {file_path} does not exist[/red]")
                return
            
            # Perform analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("🔍 Analyzing file...", total=None)
                analysis = self.agent.code_analyzer.analyze_file(file_obj)
            
            # Display analysis results
            self._display_file_analysis(analysis)
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing file: {e}[/red]")

    def _display_file_analysis(self, analysis):
        """Display comprehensive file analysis results"""
        # Main analysis table
        table = Table(title=f"[bold cyan]📊 Analysis: {analysis.file_path}[/bold cyan]", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Language", analysis.language)
        table.add_row("Lines of Code", str(analysis.lines_of_code))
        table.add_row("Complexity Score", str(analysis.complexity_score))
        table.add_row("Functions", str(len([e for e in analysis.elements if e.type == 'function'])))
        table.add_row("Classes", str(len([e for e in analysis.elements if e.type == 'class'])))
        table.add_row("Dependencies", str(len(analysis.dependencies)))
        table.add_row("Analysis Time", f"{analysis.analysis_time:.3f}s")
        
        self.console.print(table)
        
        # Code elements
        if analysis.elements:
            self.console.print("\n[bold cyan]📋 Code Elements:[/bold cyan]")
            elements_table = Table(box=box.SIMPLE)
            elements_table.add_column("Type", style="yellow")
            elements_table.add_column("Name", style="white")
            elements_table.add_column("Lines", style="dim")
            elements_table.add_column("Complexity", style="red")
            
            for element in analysis.elements[:10]:  # Show top 10
                complexity_str = str(element.complexity) if element.complexity else "N/A"
                elements_table.add_row(
                    element.type.title(),
                    element.name,
                    f"{element.line_start}-{element.line_end}",
                    complexity_str
                )
            
            self.console.print(elements_table)
        
        # Issues
        if analysis.issues:
            self.console.print(f"\n[bold red]⚠️  Issues Found ({len(analysis.issues)}):[/bold red]")
            for issue in analysis.issues[:5]:  # Show top 5 issues
                severity_color = {"error": "red", "warning": "yellow", "info": "blue"}.get(issue.get('severity', 'info'), 'white')
                line_info = f" (line {issue['line']})" if 'line' in issue else ""
                self.console.print(f"  • [{severity_color}]{issue.get('message', 'Unknown issue')}{line_info}[/{severity_color}]")
        
        # Suggestions
        if analysis.suggestions:
            self.console.print(f"\n[bold green]💡 Suggestions ({len(analysis.suggestions)}):[/bold green]")
            for suggestion in analysis.suggestions[:3]:  # Show top 3 suggestions
                self.console.print(f"  • [green]{suggestion}[/green]")
        
        # Dependencies
        if analysis.dependencies:
            self.console.print(f"\n[bold blue]📦 Dependencies ({len(analysis.dependencies)}):[/bold blue]")
            deps_text = ", ".join(analysis.dependencies[:10])  # Show first 10
            if len(analysis.dependencies) > 10:
                deps_text += f" ... and {len(analysis.dependencies) - 10} more"
            self.console.print(f"  {deps_text}")

    def _is_coding_request(self, message: str) -> bool:
        """Check if the user is requesting code generation or fixing"""
        coding_keywords = [
            'code', 'write', 'create', 'generate', 'implement', 'add', 'fix', 'correct',
            'modify', 'change', 'update', 'improve', 'build', 'make', 'develop'
        ]
        message_lower = message.lower()
        has_coding = any(re.search(r'\b' + re.escape(keyword) + r'\b', message_lower) for keyword in coding_keywords)
        has_constructs = any(re.search(r'\b' + re.escape(construct) + r'\b', message_lower) for construct in [
            'function', 'class', 'method', 'script', 'program', 'algorithm'
        ])
        return has_coding or has_constructs

    def _handle_coding_request(self, message: str):
        """Handle coding/fixing requests by automatically writing to files"""
        context = self.get_current_context()

        # Try to extract file path from message
        file_path = self._extract_file_from_message(message, context)

        if not file_path:
            # Ask user which file to modify
            file_path = self.console.input("[bold cyan]📝 Which file should I modify/create? [/bold cyan] ").strip()
            if not file_path:
                self.console.print("[red]No file specified. Please try again.[/red]")
                return

            file_obj = Path(file_path)
            if not file_obj.exists():
                directory_files = [f for f in os.listdir('.') if os.path.isfile(f)]
                close_matches = difflib.get_close_matches(file_path, directory_files, n=3, cutoff=0.6)
                if close_matches:
                    self.console.print("[yellow]File not found. Did you mean one of these?[/yellow]")
                    for match in close_matches:
                        self.console.print(f"  - {match}")
                    corrected = self.console.input("[bold cyan]Enter correct filename (or press enter to create new): [/bold cyan] ").strip()
                    if corrected:
                        file_path = corrected
                        file_obj = Path(file_path)

            if not file_obj.exists():
                if Confirm.ask(f"[bold yellow]File {file_path} does not exist. Create it?[/bold yellow]"):
                    file_obj.touch()
                    self.console.print(f"[green]Created new file {file_path}[/green]")
                else:
                    self.console.print("[red]Operation cancelled.[/red]")
                    return

            # Handle the file editing
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task("🤖 Generating code...", total=None)

                    # Use the agent's file editing capability
                    if self.use_optimized_agent:
                        # Use smart modification with conflict detection
                        result = self.agent.smart_modify_file(file_path, message, backup=True)
                        if result["success"]:
                            # Format the enhanced result
                            formatted_result = f"✅ Successfully updated {file_path}\n\n"
                            formatted_result += f"📊 {result['changes_summary']}\n"
                            if result.get('conflicts'):
                                formatted_result += f"⚠️ Resolved {len(result['conflicts'])} potential conflicts\n"
                            if result['post_analysis'].suggestions:
                                formatted_result += f"💡 {len(result['post_analysis'].suggestions)} improvement suggestions available"
                            result = formatted_result
                        else:
                            result = f"❌ Failed to update {file_path}: {result['error']}"
                    else:
                        result = self.agent.handle_file_edit_with_context(message, context)
                    
                    # Track current file
                    self.current_file = file_path

                # Display result
                if "Successfully updated" in result or "✅" in result:
                    self.console.print(f"[green]{result}[/green]")
                else:
                    self.console.print(f"[yellow]{result}[/yellow]")

            except Exception as e:
                self.console.print(f"❌ [red]Error handling coding request: {e}[/red]")

    def _extract_file_from_message(self, message: str, context: Dict[str, Any] = None) -> str:
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

        # Check if agent has a last file mentioned
        if hasattr(self.agent, 'last_file_mentioned') and self.agent.last_file_mentioned:
            return self.agent.last_file_mentioned

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

    def _was_file_assumed(self, message: str, file_path: str) -> bool:
        """Check if the file path was assumed (not explicitly mentioned with extension)"""
        import re
        from pathlib import Path

        # If the message contains the exact file path with extension, it wasn't assumed
        if file_path in message:
            return False

        # Check if the filename without extension appears in the message
        filename_without_ext = Path(file_path).stem
        if filename_without_ext in message.lower():
            # Check if any file extension was mentioned in the original message
            extension_pattern = r'\.' + '|'.join(['py', 'js', 'ts', 'java', 'cpp', 'c', 'go', 'rs', 'php', 'rb', 'cs', 'swift', 'kt', 'scala', 'r', 'sql', 'html', 'css', 'scss', 'vue', 'jsx', 'tsx', 'json', 'yaml', 'yml', 'md', 'txt'])
            if re.search(extension_pattern, message.lower()):
                return False
            return True

        return False

    def get_current_context(self):
        """Get current working directory context for chat mode"""
        context = {
            'cwd': os.getcwd(),
            'files': []
        }
        try:
            current_dir = Path('.')
            for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
                files = list(current_dir.glob(f'**/*{ext}'))[:5]
                context['files'].extend([str(f) for f in files])
        except Exception:
            pass
        return context

    def show_goodbye(self):
        """Show beautiful goodbye message"""
        goodbye = """
+==============================================================================+
|                                                                              |
|                    Thank you for using Conflict DeepCode!                   |
|                                                                              |
|                    Your AI coding companion is always here                   |
|                    when you need assistance with your code.                  |
|                                                                              |
|                    Happy coding!                                             |
|                                                                              |
+==============================================================================+
        """

        panel = Panel(
            Align.center(Text(goodbye, style="bold cyan")),
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)

def main():
    """Main entry point for the conversational terminal UI"""
    ui = ConflictDeepCodeUI()
    ui.start_interactive_session()

if __name__ == '__main__':
    main()
