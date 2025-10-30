"""
Pretty printing utilities for code and terminal output.
"""
try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import TerminalFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class CodePrinter:
    """Pretty print code with syntax highlighting in the terminal."""
    
    def __init__(self, use_rich=True):
        self.use_rich = use_rich and RICH_AVAILABLE
        if self.use_rich:
            self.console = Console()
    
    def print_code(self, code: str, language: str = "python", title: str = None, line_numbers: bool = True):
        """
        Print code with syntax highlighting.
        
        Args:
            code: The code to print
            language: Programming language (python, html, javascript, etc.)
            title: Optional title to display above the code
            line_numbers: Whether to show line numbers
        """
        if not code or not code.strip():
            return
        
        # Truncate very long code for display
        max_lines = 50
        lines = code.split('\n')
        truncated = False
        if len(lines) > max_lines:
            code = '\n'.join(lines[:max_lines])
            truncated = True
        
        if self.use_rich:
            self._print_with_rich(code, language, title, line_numbers, truncated)
        elif PYGMENTS_AVAILABLE:
            self._print_with_pygments(code, language, title, truncated)
        else:
            self._print_plain(code, title, truncated)
    
    def _print_with_rich(self, code: str, language: str, title: str, line_numbers: bool, truncated: bool):
        """Print using Rich library."""
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=line_numbers,
            word_wrap=False
        )
        
        if title:
            panel = Panel(syntax, title=f"[bold blue]{title}[/bold blue]", border_style="blue")
            self.console.print(panel)
        else:
            self.console.print(syntax)
        
        if truncated:
            self.console.print("[dim yellow]... (output truncated)[/dim yellow]")
    
    def _print_with_pygments(self, code: str, language: str, title: str, truncated: bool):
        """Print using Pygments."""
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except:
            try:
                lexer = guess_lexer(code)
            except:
                self._print_plain(code, title, truncated)
                return
        
        formatter = TerminalFormatter()
        highlighted = highlight(code, lexer, formatter)
        
        if title:
            print(f"\n{'=' * 60}")
            print(f"  {title}")
            print('=' * 60)
        
        print(highlighted)
        
        if truncated:
            print("... (output truncated)")
    
    def _print_plain(self, code: str, title: str, truncated: bool):
        """Fallback plain text printing."""
        if title:
            print(f"\n{'=' * 60}")
            print(f"  {title}")
            print('=' * 60)
        
        print(code)
        
        if truncated:
            print("... (output truncated)")
    
    def print_review(self, review: str, title: str = "Code Review"):
        """Print a code review with markdown formatting."""
        if not review or not review.strip():
            return
        
        # Truncate very long reviews
        max_chars = 1000
        truncated = False
        if len(review) > max_chars:
            review = review[:max_chars]
            truncated = True
        
        if self.use_rich:
            if truncated:
                review += "\n\n... (review truncated)"
            
            md = Markdown(review)
            panel = Panel(md, title=f"[bold green]{title}[/bold green]", border_style="green")
            self.console.print(panel)
        else:
            print(f"\n{'=' * 60}")
            print(f"  {title}")
            print('=' * 60)
            print(review)
            if truncated:
                print("... (review truncated)")
    
    def print_status(self, message: str, style: str = "info"):
        """
        Print a status message with styling.
        
        Args:
            message: The message to print
            style: One of: info, success, warning, error
        """
        if self.use_rich:
            style_map = {
                "info": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red"
            }
            color = style_map.get(style, "white")
            self.console.print(f"[{color}]{message}[/{color}]")
        else:
            print(message)


# Global instance
_printer = None

def get_code_printer() -> CodePrinter:
    """Get or create the global code printer instance."""
    global _printer
    if _printer is None:
        _printer = CodePrinter()
    return _printer


def print_code(code: str, language: str = "python", title: str = None):
    """Convenience function to print code."""
    get_code_printer().print_code(code, language, title)


def print_review(review: str, title: str = "Code Review"):
    """Convenience function to print a review."""
    get_code_printer().print_review(review, title)


def print_status(message: str, style: str = "info"):
    """Convenience function to print a status message."""
    get_code_printer().print_status(message, style)

