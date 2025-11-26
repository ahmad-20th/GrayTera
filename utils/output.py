"""
Simple colored console output utilities
"""

class Colors:
    """ANSI color codes"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def success(msg: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}[✓]{Colors.RESET} {msg}")


def error(msg: str):
    """Print error message in red"""
    print(f"{Colors.RED}[!]{Colors.RESET} {msg}")


def warning(msg: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")


def info(msg: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}[*]{Colors.RESET} {msg}")


def status(msg: str):
    """Print status message in cyan"""
    print(f"{Colors.CYAN}[→]{Colors.RESET} {msg}")


def debug(msg: str):
    """Print debug message in gray"""
    print(f"{Colors.GRAY}[DEBUG]{Colors.RESET} {msg}")