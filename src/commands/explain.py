"""
Explain command handler for DeepCode
Handles code explanation functionality
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.agent import DeepCodeAgent

def explain_handler(ctx, file_path: str, detail: str = "basic"):
    """Handle explain command"""
    console = ctx.obj['console']
    config = ctx.obj['config']
    
    # Validate file exists
    file_obj = Path(file_path)
    if not file_obj.exists():
        console.print(f"❌ File not found: [bold red]{file_path}[/bold red]")
        return False
    
    console.print(f"📖 Explaining: [bold cyan]{file_path}[/bold cyan]")
    console.print(f"🔍 Detail level: [italic]{detail}[/italic]")
    
    # Initialize agent
    agent = DeepCodeAgent(config)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing code...", total=None)
        
        try:
            # Explain the file
            result = agent.explain_file(file_path, detail)
            
            if result['success']:
                progress.update(task, description="✅ Analysis completed!")
                
                console.print(f"\n✅ Code explanation generated!")
                
                # Show file info
                file_size = file_obj.stat().st_size
                console.print(f"📊 File size: {file_size} bytes")
                
                # Show explanation
                if result.get('explanation'):
                    console.print("\n💡 Code Explanation:")
                    console.print(Panel(result['explanation'], title="AI Analysis", expand=False))
                
                # Show code preview if verbose
                if ctx.obj['verbose']:
                    _show_code_preview(console, file_obj, file_path)
                
            else:
                progress.update(task, description="❌ Explanation failed")
                console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            progress.stop()
            console.print("\n⚠️  Explanation cancelled by user")
            return False
        except Exception as e:
            progress.update(task, description="❌ Explanation failed")
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
        if len(lines) > 50:
            content = '\n'.join(lines[:50]) + '\n... (truncated)'
        
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
