"""
Modify command handler for DeepCode CLI
"""

from pathlib import Path
from core.enhanced_agent import EnhancedDeepCodeAgent
from utils.config import Config

def modify_handler(ctx, file, description, backup=True):
    """Handle modify command"""
    try:
        # Get config from context
        config = ctx.obj['config']
        console = ctx.obj['console']

        # Initialize enhanced agent
        agent = EnhancedDeepCodeAgent(config)

        # Modify the file
        result = agent.modify_file(file, description, backup)

        if result.get('success'):
            console.print(f"✅ Successfully modified {file}")
            if 'changes_summary' in result:
                console.print(f"📊 Changes: {result['changes_summary']}")
            if result.get('backup_created'):
                console.print("💾 Backup created")
        else:
            console.print(f"❌ Failed to modify {file}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        console = ctx.obj['console']
        console.print(f"[red]Error in modify command: {e}[/red]")