"""
Test command handler for DeepCode
Handles test generation functionality
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.agent import DeepCodeAgent

def test_handler(ctx, file_path: str, framework: str = None, coverage: bool = False):
    """Handle test command"""
    console = ctx.obj['console']
    config = ctx.obj['config']
    
    # Validate file exists
    file_obj = Path(file_path)
    if not file_obj.exists():
        console.print(f"❌ File not found: [bold red]{file_path}[/bold red]")
        return False
    
    console.print(f"🧪 Generating tests for: [bold cyan]{file_path}[/bold cyan]")
    if framework:
        console.print(f"🔧 Framework: [italic]{framework}[/italic]")
    if coverage:
        console.print("📊 Coverage annotations will be included")
    
    # Initialize agent
    agent = DeepCodeAgent(config)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating tests...", total=None)
        
        try:
            # Generate tests
            result = agent.generate_tests(file_path, framework)
            
            if result['success']:
                progress.update(task, description="✅ Tests generated!")
                
                console.print(f"\n✅ Tests generated successfully!")
                
                # Show test file info
                test_file = Path(result['test_file'])
                if test_file.exists():
                    test_size = test_file.stat().st_size
                    console.print(f"📄 Test file: {result['test_file']}")
                    console.print(f"📊 Test file size: {test_size} bytes")
                
                # Show test content preview
                if result.get('tests') and ctx.obj['verbose']:
                    _show_test_preview(console, result['tests'], result['test_file'])
                
                # Show next steps
                _show_next_steps(console, file_path, result['test_file'], framework)
                
            else:
                progress.update(task, description="❌ Test generation failed")
                console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            progress.stop()
            console.print("\n⚠️  Test generation cancelled by user")
            return False
        except Exception as e:
            progress.update(task, description="❌ Test generation failed")
            console.print(f"\n❌ Unexpected error: {str(e)}")
            if ctx.obj['verbose']:
                import traceback
                console.print(traceback.format_exc())
            return False
    
    return True

def _show_test_preview(console: Console, tests: str, test_file: str):
    """Show test content preview with syntax highlighting"""
    try:
        # Limit content for preview
        lines = tests.split('\n')
        if len(lines) > 40:
            content = '\n'.join(lines[:40]) + '\n... (truncated)'
        else:
            content = tests
        
        # Detect file type for syntax highlighting
        test_file_obj = Path(test_file)
        syntax = Syntax(
            content,
            lexer_name=_get_lexer_name(test_file_obj.suffix),
            theme="monokai",
            line_numbers=True
        )
        
        console.print(f"\n📄 Test preview ({test_file}):")
        console.print(syntax)
        
    except Exception as e:
        console.print(f"⚠️  Could not show test preview: {e}")

def _show_next_steps(console: Console, source_file: str, test_file: str, framework: str):
    """Show suggested next steps after test generation"""
    file_obj = Path(source_file)
    file_type = _detect_file_type(file_obj.suffix)
    
    steps = []
    
    if file_type == 'python':
        if framework == 'pytest':
            steps = [
                f"Run tests: pytest {test_file}",
                f"Run with coverage: pytest --cov={file_obj.stem} {test_file}",
                f"Run specific test: pytest {test_file}::test_function_name"
            ]
        else:
            steps = [
                f"Run tests: python -m unittest {test_file}",
                f"Run all tests: python -m unittest discover",
                f"Run with coverage: coverage run -m unittest {test_file}"
            ]
    elif file_type in ['javascript', 'typescript']:
        if framework == 'jest':
            steps = [
                f"Run tests: npm test {test_file}",
                f"Run with coverage: npm test -- --coverage",
                f"Run in watch mode: npm test -- --watch"
            ]
        else:
            steps = [
                f"Run tests: node {test_file}",
                f"Run with mocha: mocha {test_file}",
                f"Run with coverage: nyc mocha {test_file}"
            ]
    else:
        steps = [
            f"Review test file: {test_file}",
            f"Run tests with appropriate framework",
            f"Add to CI/CD pipeline"
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
