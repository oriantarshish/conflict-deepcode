"""
Review command handler for DeepCode
Handles code review functionality
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.agent import DeepCodeAgent

def review_handler(ctx, file_path: str, style: str = "all"):
    """Handle review command"""
    console = ctx.obj['console']
    config = ctx.obj['config']
    
    # Validate file exists
    file_obj = Path(file_path)
    if not file_obj.exists():
        console.print(f"❌ File not found: [bold red]{file_path}[/bold red]")
        return False
    
    console.print(f"🔍 Reviewing: [bold cyan]{file_path}[/bold cyan]")
    console.print(f"📋 Review style: [italic]{style}[/italic]")
    
    # Initialize agent
    agent = DeepCodeAgent(config)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing code quality...", total=None)
        
        try:
            # Review the file
            result = agent.review_file(file_path, style)
            
            if result['success']:
                progress.update(task, description="✅ Review completed!")
                
                console.print(f"\n✅ Code review generated!")
                
                # Show file info
                file_size = file_obj.stat().st_size
                console.print(f"📊 File size: {file_size} bytes")
                
                # Show review
                if result.get('review'):
                    console.print("\n🔍 Code Review:")
                    console.print(Panel(result['review'], title="AI Review", expand=False))
                
                # Show code preview if verbose
                if ctx.obj['verbose']:
                    _show_code_preview(console, file_obj, file_path)
                
                # Show next steps
                _show_next_steps(console, file_path, style)
                
            else:
                progress.update(task, description="❌ Review failed")
                console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            progress.stop()
            console.print("\n⚠️  Review cancelled by user")
            return False
        except Exception as e:
            progress.update(task, description="❌ Review failed")
            console.print(f"\n❌ Unexpected error: {str(e)}")
            if ctx.obj['verbose']:
                import traceback
                console.print(traceback.format_exc())
            return False
    
    return True

def _show_code_preview(console: Console, file_obj: Path, file_path: str):
    """Show code preview with syntax highlighting"""
    try:
        content = file_obj.read_text(encoding='utf-8')
        
        # Limit content for preview
        lines = content.split('\n')
        if len(lines) > 30:
            content = '\n'.join(lines[:30]) + '\n... (truncated)'
        
        syntax = Syntax(
            content,
            lexer_name=_get_lexer_name(file_obj.suffix),
            theme="monokai",
            line_numbers=True
        )
        
        console.print(f"\n📄 Code preview ({file_path}):")
        console.print(syntax)
        
    except Exception as e:
        console.print(f"⚠️  Could not show code preview: {e}")

def _show_next_steps(console: Console, file_path: str, style: str):
    """Show suggested next steps after review"""
    file_obj = Path(file_path)
    file_type = _detect_file_type(file_obj.suffix)
    
    steps = []
    
    if style == "security":
        steps = [
            f"Fix security issues: deepcode modify {file_path} 'fix security vulnerabilities'",
            f"Run security scan: deepcode test {file_path} --security",
            "Review security best practices"
        ]
    elif style == "performance":
        steps = [
            f"Optimize performance: deepcode modify {file_path} 'optimize for performance'",
            f"Profile the code: deepcode test {file_path} --performance",
            "Benchmark improvements"
        ]
    elif style == "maintainability":
        steps = [
            f"Refactor for maintainability: deepcode modify {file_path} 'improve code structure'",
            f"Add documentation: deepcode modify {file_path} 'add comprehensive documentation'",
            "Update tests and examples"
        ]
    else:  # all
        steps = [
            f"Address issues: deepcode modify {file_path} 'implement review suggestions'",
            f"Generate tests: deepcode test {file_path}",
            f"Get detailed explanation: deepcode explain {file_path} --detail deep"
        ]
    
    console.print("\n🚀 Next steps:")
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. [bold green]{step}[/bold green]")

def _get_lexer_name(extension: str) -> str:
    """Get Pygments lexer name for file extension"""
    lexer_map = {
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
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql',
        '.yaml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.md': 'markdown',
        '.sh': 'bash'
    }
    return lexer_map.get(extension.lower(), 'text')

def _detect_file_type(extension: str) -> str:
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
        '.swift': 'swift'
    }
    return type_map.get(extension.lower(), 'text')
