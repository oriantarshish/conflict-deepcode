"""
Create command handler for DeepCode
Handles file and project creation
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.agent import DeepCodeAgent

def create_handler(ctx, target: str, file_type: str = None, template: str = None):
    """Handle create command"""
    console = ctx.obj['console']
    config = ctx.obj['config']
    
    console.print(f"🔨 Creating: [bold cyan]{target}[/bold cyan]")
    
    # Initialize agent
    agent = DeepCodeAgent(config)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing requirements...", total=None)
        
        try:
            # Create the file/project
            result = agent.create_file(target, file_type, template)
            
            if result['success']:
                progress.update(task, description="✅ Creation completed!")
                
                if 'project' in result:
                    # Project creation
                    console.print(f"\n✅ Project '{result['project']}' created successfully!")
                    
                    if result.get('files_created'):
                        console.print("\n📁 Files created:")
                        for file_path in result['files_created']:
                            console.print(f"  • {file_path}")
                    
                    # Show explanation
                    if result.get('explanation'):
                        console.print("\n💡 Project Structure:")
                        console.print(Panel(result['explanation'], title="AI Explanation", expand=False))
                
                else:
                    # Single file creation
                    file_path = result['file']
                    console.print(f"\n✅ File '{file_path}' created successfully!")
                    
                    # Show created content with syntax highlighting
                    if result.get('content'):
                        file_obj = Path(file_path)
                        syntax = Syntax(
                            result['content'][:1000] + ("..." if len(result['content']) > 1000 else ""),
                            lexer_name=_get_lexer_name(file_obj.suffix),
                            theme="monokai",
                            line_numbers=True
                        )
                        console.print(f"\n📄 Content preview:")
                        console.print(syntax)
                    
                    # Show explanation
                    if result.get('explanation') and ctx.obj['verbose']:
                        console.print("\n💡 AI Explanation:")
                        console.print(Panel(result['explanation'], title="Creation Details", expand=False))
                
                # Provide next steps
                _show_next_steps(console, target, result)
                
            else:
                progress.update(task, description="❌ Creation failed")
                console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            progress.stop()
            console.print("\n⚠️  Creation cancelled by user")
            return False
        except Exception as e:
            progress.update(task, description="❌ Creation failed")
            console.print(f"\n❌ Unexpected error: {str(e)}")
            if ctx.obj['verbose']:
                import traceback
                console.print(traceback.format_exc())
            return False
    
    return True

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

def _show_next_steps(console: Console, target: str, result: dict):
    """Show suggested next steps after creation"""
    target_path = Path(target)
    
    steps = []
    
    if result.get('project'):
        # Project next steps
        steps = [
            f"cd {target}",
            "deepcode init",
            "deepcode status",
            "Start coding with: deepcode chat"
        ]
    else:
        # Single file next steps
        file_type = _detect_file_type(target_path.suffix)
        
        if file_type == 'python':
            steps = [
                f"Edit the file: {target}",
                f"Run tests: deepcode test {target}",
                f"Get explanation: deepcode explain {target}"
            ]
        elif file_type in ['javascript', 'typescript']:
            steps = [
                f"Edit the file: {target}",
                f"Run tests: deepcode test {target} --framework jest",
                f"Get review: deepcode review {target}"
            ]
        else:
            steps = [
                f"Edit the file: {target}",
                f"Get explanation: deepcode explain {target}",
                f"Modify if needed: deepcode modify {target} 'your changes'"
            ]
    
    if steps:
        console.print("\n🚀 Next steps:")
        for i, step in enumerate(steps, 1):
            console.print(f"  {i}. [bold green]{step}[/bold green]")

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