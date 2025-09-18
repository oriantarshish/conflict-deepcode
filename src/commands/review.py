"""
Review command handler for DeepCode CLI
"""

from pathlib import Path
from core.enhanced_agent import EnhancedDeepCodeAgent
from utils.config import Config

def review_handler(ctx, file, style='all'):
    """Handle review command"""
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

        # Generate review based on style
        review_title = f"🔍 Code Review for {file}"
        if style == 'security':
            review_content = f"🛡️ Security Review:\n\n{content[:500]}{'...' if len(content) > 500 else ''}\n\n⚠️ Security analysis would be performed here."
        elif style == 'performance':
            review_content = f"⚡ Performance Review:\n\n{content[:500]}{'...' if len(content) > 500 else ''}\n\n📊 Performance analysis would be performed here."
        elif style == 'maintainability':
            review_content = f"🛠️ Maintainability Review:\n\n{content[:500]}{'...' if len(content) > 500 else ''}\n\n🔧 Maintainability analysis would be performed here."
        else:  # 'all'
            review_content = f"📋 Comprehensive Review:\n\n{content[:500]}{'...' if len(content) > 500 else ''}\n\n✅ General code review would be performed here."

        console.print(f"{review_title}\n\n{review_content}")

    except Exception as e:
        console = ctx.obj['console']
        console.print(f"[red]Error in review command: {e}[/red]")