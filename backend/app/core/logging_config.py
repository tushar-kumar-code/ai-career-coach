import logging
import sys
import time
from typing import Optional

# ANSI Color Codes for terminal
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"


class ColoredTerminalFormatter(logging.Formatter):
    """Custom logging formatter that renders colorful, human-readable terminal logs."""

    LEVEL_MAP = {
        logging.DEBUG: f"{CYAN}[DEBUG]{RESET}",
        logging.INFO: f"{GREEN}[INFO]{RESET}",
        logging.WARNING: f"{YELLOW}{BOLD}[WARN]{RESET}",
        logging.ERROR: f"{RED}{BOLD}[ERROR]{RESET}",
        logging.CRITICAL: f"{BG_RED}{WHITE}{BOLD}[CRITICAL]{RESET}",
    }

    def format(self, record: logging.LogRecord) -> str:
        timestamp = time.strftime("%H:%M:%S", time.localtime(record.created))
        time_str = f"{DIM}{timestamp}{RESET}"
        level_str = self.LEVEL_MAP.get(record.levelno, f"[{record.levelname}]")
        
        # Colorize logger name based on subsystem
        name = record.name
        if "main" in name or "middleware" in name:
            name_colored = f"{CYAN}{name}{RESET}"
        elif "ai" in name or "groq" in name or "gemini" in name:
            name_colored = f"{MAGENTA}{name}{RESET}"
        elif "auth" in name or "security" in name:
            name_colored = f"{YELLOW}{name}{RESET}"
        elif "database" in name or "init_db" in name:
            name_colored = f"{BLUE}{name}{RESET}"
        elif "frontend" in name:
            name_colored = f"{CYAN}{BOLD}[FRONTEND]{RESET}"
        else:
            name_colored = f"{DIM}{name}{RESET}"

        message = record.getMessage()

        # Format with color tags in message if present
        if record.levelno >= logging.ERROR and record.exc_info:
            base = f"{time_str} {level_str} {name_colored} - {message}"
            exc_text = self.formatException(record.exc_info)
            return f"{base}\n{RED}{exc_text}{RESET}"

        return f"{time_str} {level_str} {name_colored} - {message}"


def setup_terminal_logging(level: int = logging.INFO):
    """Configure root logger and standard library handlers for beautiful terminal output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove default handlers to prevent duplicate output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredTerminalFormatter())
    root_logger.addHandler(console_handler)

    # Adjust third-party loggers so they don't spam
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Handled by our custom middleware
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Ensure UTF-8 stdout on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Print startup banner safely
    try:
        print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{GREEN}  🚀 AI Career Coach - Live Terminal Logging Enabled{RESET}")
        print(f"{DIM}  All backend API calls, AI prompts, and frontend events will show here.{RESET}")
        print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════\n{RESET}")
    except Exception:
        print("\n=== AI Career Coach - Live Terminal Logging Enabled ===\n")
