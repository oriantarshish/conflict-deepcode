#!/usr/bin/env python3
"""
DeepCode - Free AI Coding Assistant
Main CLI entry point
"""

import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from core.agent import DeepCodeAgent
from core.optimized_agent import OptimizedDeepCodeAgent
from core.enhanced_agent import EnhancedDeepCodeAgent
from core.ollama_client import OllamaClient
from core.file_manager import FileManager
from utils.config import Config
from commands import create, modify, explain, review, test
from terminal_ui import ConflictDeepCodeUI

console = Console()

@click.group()
@click.version_option(version="1.1.0")
@click.option('--config', '-c', help='Config file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--unsafe', is_flag=True, help='Disable safety confirmations for file operations')
@click.option('--num-ctx', type=int, help='Override model context window (num_ctx)')
@click.option('--num-predict', type=int, help='Override max tokens to predict')
@click.option('--timeout', type=int, help='Override request timeout (seconds)')
@click.pass_context
def cli(ctx, config, verbose, unsafe, num_ctx, num_predict, timeout):
    """DeepCode - Free AI Coding Assistant powered by DeepSeek V2 Coder"""
    ctx.ensure_object(dict)
    
    # Initialize configuration
    config_path = config or os.path.expanduser('~/.conflict-deepcode/config.yaml')
    ctx.obj['config'] = Config(config_path)
    ctx.obj['verbose'] = verbose

    # Initialize console
    ctx.obj['console'] = console

    # Apply CLI overrides (do not persist by default)
    if unsafe:
        ctx.obj['config'].set('agent.enable_dangerous_action_confirmation', False)
    if num_ctx:
        ctx.obj['config'].set('ollama.num_ctx', num_ctx)
        # Backward-compat: keep max_tokens in sync if present
        ctx.obj['config'].set('ollama.max_tokens', num_ctx)
    if num_predict:
        ctx.obj['config'].set('ollama.num_predict', num_predict)
    if timeout:
        ctx.obj['config'].set('ollama.timeout', timeout)
    
    # Check Ollama connection on startup
    try:
        ollama = OllamaClient(ctx.obj['config'])
        if not ollama.is_available():
            console.print("[red]❌ Ollama is not running or not accessible[/red]")
            console.print("Please ensure Ollama is installed and running:")
            console.print("  1. Install Ollama: https://ollama.ai")
            console.print("  2. Run: ollama serve")
            console.print("  3. Pull model: ollama pull deepseek-coder-v2")
            sys.exit(1)
            
        if not ollama.has_model():
            console.print("[yellow]⚠️  DeepSeek Coder V2 model not found[/yellow]")
            if click.confirm("Do you want to download it now?"):
                ollama.pull_model()
            else:
                console.print("[red]Model required to continue[/red]")
                sys.exit(1)
                
    except Exception as e:
        if verbose:
            console.print(f"[red]Connection error: {e}[/red]")
        else:
            console.print("[red]❌ Unable to connect to Ollama[/red]")
        sys.exit(1)

@cli.command()
@click.argument('target')
@click.option('--type', '-t', help='Project type (python, javascript, etc.)')
@click.option('--template', help='Template to use')
@click.pass_context
def create_cmd(ctx, target, type, template):
    """Create new files or projects"""
    create.create_handler(ctx, target, type, template)

@cli.command()
@click.argument('file')
@click.argument('description')
@click.option('--backup/--no-backup', default=True, help='Create backup before modifying')
@click.pass_context
def modify_cmd(ctx, file, description, backup):
    """Modify existing code files"""
    modify.modify_handler(ctx, file, description, backup)

@cli.command()
@click.argument('file')
@click.option('--detail', '-d', type=click.Choice(['basic', 'detailed', 'deep']), default='basic')
@click.pass_context
def explain_cmd(ctx, file, detail):
    """Explain code functionality"""
    explain.explain_handler(ctx, file, detail)

@cli.command()
@click.argument('file')
@click.option('--style', type=click.Choice(['security', 'performance', 'maintainability', 'all']), default='all')
@click.pass_context
def review_cmd(ctx, file, style):
    """Review code and provide suggestions"""
    review.review_handler(ctx, file, style)

@cli.command()
@click.argument('file')
@click.option('--framework', help='Testing framework to use')
@click.option('--coverage', is_flag=True, help='Include coverage annotations')
@click.pass_context
def test_cmd_handler(ctx, file, framework, coverage):
    """Generate tests for code files"""
    test.test_handler(ctx, file, framework, coverage)


@cli.command()
@click.option('--agent', '-a', type=click.Choice(['basic', 'optimized', 'enhanced']), default='enhanced',
              help='Agent type: basic (legacy), optimized (advanced analysis), enhanced (super-intelligent with memory)')
@click.option('--cache/--no-cache', default=True, help='Enable response caching for faster interactions')
@click.option('--analysis/--no-analysis', default=True, help='Enable advanced code analysis')
@click.pass_context
def chat(ctx, agent, cache, analysis):
    """Start interactive coding session with AI assistant"""
    if agent == 'enhanced':
        console.print(Panel.fit("🧠 DeepCode Enhanced Interactive Session", style="magenta"))
        console.print("Super-intelligent with: Advanced Memory • Context Analysis • Smart File Operations • Learning")
        ai_agent = EnhancedDeepCodeAgent(ctx.obj['config'])

    elif agent == 'optimized':
        console.print(Panel.fit("🚀 DeepCode Optimized Interactive Session", style="blue"))
        console.print("Enhanced with: Advanced Analysis • Smart Caching • Conflict Detection")
        ai_agent = OptimizedDeepCodeAgent(ctx.obj['config'])

        # Configure optimization settings
        ai_agent.enable_caching = cache
        ai_agent.code_analyzer.cache = {} if not cache else ai_agent.code_analyzer.cache

    else:  # basic
        console.print(Panel.fit("🤖 DeepCode Interactive Session (Basic)", style="green"))
        ai_agent = DeepCodeAgent(ctx.obj['config'])
    
    console.print("Type 'exit' to quit, 'help' for commands, 'stats' for performance info\n")

    while True:
        try:
            user_input = input("💬 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("👋 Goodbye!")
                break

            if user_input.lower() == 'help':
                help_text = """
Available commands in chat:
  - Describe what you want to code
  - Ask questions about existing files
  - Request explanations or reviews
  - 'stats' - Show performance statistics
  - 'clear' - Clear caches
  - 'memory' - Show conversation memory (enhanced only)
  - 'exit' - Quit session
                """
                if agent == 'enhanced':
                    help_text += """
🧠 Enhanced Agent Features:
  ✅ Super-intelligent context analysis
  ✅ Advanced memory with conversation history
  ✅ Intelligent file operations with analysis
  ✅ Learning from user patterns
  ✅ Smart project structure understanding
  ✅ Enhanced code generation with context
                    """
                elif agent == 'optimized':
                    help_text += """
🚀 Optimized Agent Features:
  ✅ Advanced code analysis with AST parsing
  ✅ Intelligent conflict detection
  ✅ Smart caching for faster responses
  ✅ Production-ready code generation
                    """
                console.print(help_text)
                continue

            if user_input.lower() == 'stats':
                if agent == 'enhanced':
                    stats = ai_agent.get_performance_stats()
                    memory_stats = {
                        'conversation_length': len(ai_agent.memory.conversation_history),
                        'file_operations': len(ai_agent.memory.file_operations),
                        'cache_size': len(ai_agent.response_cache),
                        'last_file': ai_agent.memory.session_context.get('last_file', 'None')
                    }
                    console.print(f"""
📊 Enhanced Agent Statistics:
  • Conversation history: {memory_stats['conversation_length']} messages
  • File operations: {memory_stats['file_operations']} recorded
  • Response cache: {memory_stats['cache_size']} entries
  • Last file worked on: {memory_stats['last_file']}
                    """)
                elif agent == 'optimized':
                    stats = ai_agent.get_performance_stats()
                    console.print(f"""
📊 Performance Statistics:
  • Cache size: {stats['cache_size']} responses
  • Analyzer cache: {stats['analyzer_cache_size']} files
  • Conversation length: {stats['conversation_length']} messages
  • Last file: {stats['last_file'] or 'None'}
                    """)
                else:
                    console.print("📊 Basic agent - no performance statistics available")
                continue

            if user_input.lower() == 'memory' and agent == 'enhanced':
                memory_info = f"""
🧠 Memory Status:
  • Conversation entries: {len(ai_agent.memory.conversation_history)}
  • File operations: {len(ai_agent.memory.file_operations)}
  • Learned patterns: {len(ai_agent.memory.learned_patterns)}
  • Session context: {bool(ai_agent.memory.session_context)}
                """
                console.print(memory_info)
                continue

            if user_input.lower() == 'clear':
                if agent == 'enhanced':
                    ai_agent.clear_all_caches()
                    ai_agent.memory.conversation_history.clear()
                    console.print("🧹 All caches and memory cleared!")
                elif agent == 'optimized':
                    ai_agent.clear_all_caches()
                    console.print("🧹 All caches cleared!")
                else:
                    console.print("🧹 Cache clearing not available for basic agent")
                continue

            if not user_input:
                continue

            console.print("\n🤖 DeepCode:", style="green")

            if agent == 'enhanced':
                response = ai_agent.enhanced_chat(user_input, get_current_context())
            elif agent == 'optimized':
                response = ai_agent.enhanced_chat(user_input, get_current_context())
            else:
                response = ai_agent.chat(user_input, get_current_context())

            console.print(response)
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if agent in ['optimized', 'enhanced'] and hasattr(ai_agent, 'clear_all_caches'):
                console.print("[yellow]Clearing caches and retrying...[/yellow]")
                ai_agent.clear_all_caches()

@cli.command()
@click.pass_context
def init(ctx):
    """Initialize current directory for DeepCode"""
    console.print("🚀 Initializing DeepCode in current directory...")
    
    # Create .deepcode directory
    deepcode_dir = Path('.deepcode')
    deepcode_dir.mkdir(exist_ok=True)
    
    # Create local config
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
    
    # Create gitignore entry
    gitignore = Path('.gitignore')
    gitignore_content = ""
    if gitignore.exists():
        gitignore_content = gitignore.read_text()
    
    if '.deepcode/' not in gitignore_content:
        with open(gitignore, 'a') as f:
            f.write('\n# DeepCode\n.deepcode/\n')
    
    console.print("✅ DeepCode initialized successfully!")
    console.print(f"Config: {local_config}")

@cli.command()
@click.pass_context
def status(ctx):
    """Show current project status and context"""
    console.print("📊 DeepCode Status")
    
    # Check Ollama status
    ollama = OllamaClient(ctx.obj['config'])
    if ollama.is_available():
        console.print("✅ Ollama: Connected")
        console.print(f"🤖 Model: {ollama.get_current_model()}")
    else:
        console.print("❌ Ollama: Disconnected")
    
    # Check project initialization
    if Path('.deepcode').exists():
        console.print("✅ Project: Initialized")
    else:
        console.print("⚠️  Project: Not initialized (run 'deepcode init')")
    
    # Show file count and languages
    current_dir = Path('.')
    py_files = len(list(current_dir.glob('**/*.py')))
    js_files = len(list(current_dir.glob('**/*.js')))
    total_files = len([f for f in current_dir.rglob('*') if f.is_file()])
    
    console.print(f"📁 Files: {total_files} total, {py_files} Python, {js_files} JavaScript")

@cli.command()
@click.pass_context
def ui(ctx):
    """Launch the beautiful interactive terminal UI"""
    ui = ConflictDeepCodeUI()
    ui.start_interactive_session()

@cli.command()
@click.pass_context
def dpcd(ctx):
    """Launch the dpcd chatbox interface (alias for ui)"""
    ui = ConflictDeepCodeUI()
    ui.start_interactive_session()

def get_current_context():
    """Get current working directory context for chat mode"""
    context = {
        'cwd': os.getcwd(),
        'files': []
    }
    
    # Get recent files
    try:
        current_dir = Path('.')
        for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
            files = list(current_dir.glob(f'**/*{ext}'))[:5]  # Limit to 5 per type
            context['files'].extend([str(f) for f in files])
    except:
        pass
    
    return context

if __name__ == '__main__':
    # If no arguments provided, launch the beautiful UI
    if len(sys.argv) == 1:
        ui = ConflictDeepCodeUI()
        ui.start_interactive_session()
    else:
        cli()