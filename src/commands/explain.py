"""
Explain command handler for DeepCode CLI
"""

from pathlib import Path
from core.enhanced_agent import EnhancedDeepCodeAgent
from utils.config import Config

def explain_handler(ctx, file, detail='basic'):
    """Handle explain command"""
    try:
        # Get config from context
        config = ctx.obj['config']
        console = ctx.obj['console']

        # Initialize enhanced agent
        agent = EnhancedDeepCodeAgent(config)

        # Read the file content
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[red]File {file} does not exist[/red]")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate explanation based on detail level
        if detail == 'basic':
            explanation = f"📄 Basic explanation of {file}:\n\n{content[:500]}{'...' if len(content) > 500 else ''}"
        elif detail == 'detailed':
            explanation = f"📋 Detailed explanation of {file}:\n\n{content[:1000]}{'...' if len(content) > 1000 else ''}"
        elif detail == 'deep':
            explanation = f"🔍 Deep analysis of {file}:\n\n{content}"
        else:
            explanation = f"📄 Explanation of {file}:\n\n{content[:500]}{'...' if len(content) > 500 else ''}"

        console.print(explanation)

    except Exception as e:
        console = ctx.obj['console']
        console.print(f"[red]Error in explain command: {e}[/red]")