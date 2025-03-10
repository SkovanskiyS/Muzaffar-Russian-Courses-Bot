import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Create custom theme for rich
custom_theme = Theme({
    "info": "bold cyan",
    "warning": "bold yellow", 
    "error": "bold red",
    "critical": "bold white on red"
})

console = Console(theme=custom_theme)

# Define log format - simplified and cleaner
LOG_FORMAT = "%(message)s"  # Rich will handle the formatting

# Set up logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            show_path=False
        )
    ]
)

# Get logger
logger = logging.getLogger("Bot")
logger.info("[bold green]✓[/] Logging system initialized successfully!")

# Example log messages to show formatting:
# logger.debug("Debug message")
# logger.info("Info message") 
# logger.warning("Warning message")
# logger.error("Error message")
# logger.critical("Critical message")
