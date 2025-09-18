"""
Test command handler for DeepCode CLI
"""

from pathlib import Path
from core.enhanced_agent import EnhancedDeepCodeAgent
from utils.config import Config

def test_handler(ctx, file, framework=None, coverage=False):
    """Handle test command"""
    try:
        # Get config from context
        config = ctx.obj['config']
        console = ctx.obj['console']

        # Initialize enhanced agent
        agent = EnhancedDeepCodeAgent(config)

        # Generate tests for the file
        result = agent.generate_tests(file, framework, coverage)

        if result.get('success'):
            console.print(f"✅ Successfully generated tests for {file}")
            if 'test_file' in result:
                console.print(f"📁 Test file: {result['test_file']}")
            if coverage:
                console.print("📊 Coverage analysis included")
        else:
            console.print(f"❌ Failed to generate tests for {file}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        console = ctx.obj['console']
        console.print(f"[red]Error in test command: {e}[/red]")