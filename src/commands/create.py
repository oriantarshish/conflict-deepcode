"""
Create command handler for DeepCode CLI
"""

from pathlib import Path
from core.enhanced_agent import EnhancedDeepCodeAgent
from utils.config import Config

def create_handler(ctx, target, type=None, template=None):
    """Handle create command"""
    try:
        # Get config from context
        config = ctx.obj['config']
        console = ctx.obj['console']

        # Initialize enhanced agent
        agent = EnhancedDeepCodeAgent(config)

        # Determine if target is a file or project
        target_path = Path(target)

        if target_path.suffix or not target_path.suffix:  # Assume file if has extension or no extension
            # Create single file
            result = agent.create_file(str(target_path), type, template)
            if result.get('success'):
                console.print(f"✅ Successfully created {target}")
                if 'content' in result:
                    console.print(f"📊 Content length: {len(result['content'])} characters")
            else:
                console.print(f"❌ Failed to create {target}: {result.get('error', 'Unknown error')}")
        else:
            # Create project (placeholder for now)
            console.print(f"🚧 Project creation not yet implemented for {target}")

    except Exception as e:
        console = ctx.obj['console']
        console.print(f"[red]Error in create command: {e}[/red]")