"""Buzzkill Search - Fast file search utility."""

__version__ = "0.1.0"

def main():
    """Entry point for the application."""
    from .buzzkill_search import main as app_main
    app_main()

if __name__ == "__main__":
    main() 