"""
Modify command handler for DeepCode
Handles file modifications based on user descriptions
"""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
# from rich.diff import Diff  # Not available in current rich version
from rich.panel import Panel

from core.agent import DeepCodeAgent

def modify_handler(ctx, file_path: str, description: str, backup: bool = True):
    """Handle modify command"""
    console = ctx.obj['console']
    config = ctx.obj['config']
    
    # Validate file exists
    file_obj = Path(file_path)
    if not file_obj.exists():
        console.print(f"❌ File not found: [bold red]{file_path}[/bold red]")
        return False
    
    console.print(f"🔧 Modifying: [bold cyan]{file_path}[/bold cyan]")
    console.print(f"📝 Request: [italic]{description}[/italic]")
    
    if backup:
        console.print("💾 Backup will be created before modification")
    
    # Read original content for comparison
    try:
        original_content = file_obj.read_text(encoding='utf-8')
    except Exception as e:
        console.print(f"❌ Error reading file: {e}")
        return False
    
    # Initialize agent
    agent = DeepCodeAgent(config)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing file and requirements...", total=None)
        
        try:
            # Modify the file
            result = agent.modify_file(file_path, description, backup)
            
            if result['success']:
                progress.update(task, description="✅ Modification completed!")
                
                console.print(f"\n✅ File '{file_path}' modified successfully!")
                
                # Show file size changes
                original_size = result.get('original_size', 0)
                modified_size = result.get('modified_size', 0)
                size_diff = modified_size - original_size
                
                console.print(f"📊 Size change: {original_size} → {modified_size} bytes", end="")
                if size_diff > 0:
                    console.print(f" ([green]+{size_diff}[/green])")
                elif size_diff < 0:
                    console.print(f" ([red]{size_diff}[/red])")
                else:
                    console.print(" (no change)")
                
                if result.get('backup_created'):
                    console.print("💾 Backup created successfully")
                
                # Show diff if requested
                if ctx.obj['verbose']:
                    _show_diff(console, original_content, file_obj, file_path)
                
                # Show explanation
                if result.get('explanation'):
                    console.print("\n💡 Modification Details:")
                    # Extract just the explanation part, not the full code
                    explanation_text = _extract_explanation(result['explanation'])
                    console.print(Panel(explanation_text, title="AI Explanation", expand=False))
                
                # Show next steps
                _show_next_steps(console, file_path)
                
            else:
                progress.update(task, description="❌ Modification failed")
                console.print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return False
                
        except KeyboardInterrupt:
            progress.stop()
            console.print("\n⚠️  Modification cancelled by user")
            # If backup was created, offer to restore
            if backup and file_obj.exists():
                if _confirm_restore(console):
                    _restore_from_backup(console, file_obj, agent)
            return False
        except Exception as e:
            progress.update(task, description="❌ Modification failed")
            console.print(f"\n❌ Unexpected error: {str(e)}")
            if ctx.obj['verbose']:
                import traceback
                console.print(traceback.format_exc())
            return False
    
    return True

def _show_diff(console: Console, original_content: str, file_obj: Path, file_path: str):
    """Show diff between original and modified content"""
    try:
        modified_content = file_obj.read_text(encoding='utf-8')
        
        # Simple diff display
        console.print(f"\n📊 Changes made to {file_path}:")
        console.print("Original size:", len(original_content), "bytes")
        console.print("Modified size:", len(modified_content), "bytes")
        
        # Show first few lines of changes
        original_lines = original_content.split('\n')
        modified_lines = modified_content.split('\n')
        
        if len(original_lines) != len(modified_lines):
            console.print(f"Line count changed: {len(original_lines)} → {len(modified_lines)}")
        
    except Exception as e:
        console.print(f"⚠️  Could not show diff: {e}")

def _extract_explanation(full_response: str) -> str:
    """Extract explanation from AI response, excluding code blocks"""
    lines = full_response.split('\n')
    explanation_lines = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if not in_code_block:
            # Skip lines that look like code
            if (not line.startswith('    ') and 
                not line.startswith('\t') and
                not any(keyword in line.lower() for keyword in ['def ', 'class ', 'function ', 'import '])):
                explanation_lines.append(line)
    
    explanation = '\n'.join(explanation_lines).strip()
    
    # If explanation is too long, truncate
    if len(explanation) > 500:
        explanation = explanation[:497] + "..."
    
    return explanation or "File modified according to your request."

def _show_next_steps(console: Console, file_path: str):
    """Show suggested next steps after modification"""
    file_obj = Path(file_path)
    file_type = _detect_file_type(file_obj.suffix)
    
    steps = []
    
    if file_type == 'python':
        steps = [
            f"Test the changes: python {file_path}",
            f"Run tests: deepcode test {file_path}",
            f"Get review: deepcode review {file_path}"
        ]
    elif file_type in ['javascript', 'typescript']:
        steps = [
            f"Test the changes: node {file_path}",
            f"Run tests: deepcode test {file_path}",
            f"Get review: deepcode review {file_path}"
        ]
    else:
        steps = [
            f"Review changes: cat {file_path}",
            f"Get explanation: deepcode explain {file_path}",
            f"Get review: deepcode review {file_path}"
        ]
    
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
        '.cs': 'csharp'
    }
    return type_map.get(extension.lower(), 'text')

def _confirm_restore(console: Console) -> bool:
    """Ask user if they want to restore from backup"""
    try:
        response = input("\n⚠️  Do you want to restore the original file from backup? [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    except (EOFError, KeyboardInterrupt):
        return False

def _restore_from_backup(console: Console, file_obj: Path, agent):
    """Restore file from most recent backup"""
    try:
        backups = agent.file_manager.list_backups(file_obj)
        if backups:
            latest_backup = Path(backups[0]['file'])
            agent.file_manager.restore_backup(latest_backup, file_obj)
            console.print("✅ File restored from backup")
        else:
            console.print("❌ No backup found")
    except Exception as e:
        console.print(f"❌ Failed to restore backup: {e}")