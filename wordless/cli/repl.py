"""Interactive REPL for Wordless."""

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from wordless.config import HISTORY_FILE
from wordless.cli.commands import IndexManager


class REPL:
    """Interactive command-line interface."""

    def __init__(self):
        self.manager = IndexManager()

    def run(self) -> None:
        """Start the interactive REPL loop."""
        print("🔍 Wordless — Semantic Code Search")
        print("Type 'help' for commands or 'exit' to quit.\n")

        while True:
            try:
                user_input = prompt(
                    "wordless> ",
                    history=FileHistory(str(HISTORY_FILE)),
                )
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break

            self.execute(user_input.strip())

    def execute(self, cmd_line: str) -> None:
        """Parse and execute user commands."""
        if not cmd_line:
            return

        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "index":
            if args:
                try:
                    self.manager.index(args)
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("Usage: index <path/to/repo>")

        elif cmd in ("search", "s"):
            if args:
                result = self.manager.search(args)
                print(result)
            else:
                print("Usage: search <query>")

        elif cmd == "status":
            print(self.manager.status())

        elif cmd == "help":
            self.show_help()

        elif cmd in ("exit", "quit"):
            raise KeyboardInterrupt

        else:
            print(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    def show_help(self) -> None:
        """Display available commands."""
        help_text = """
Available Commands:
  index <path>           Index a Python repository
  search <query>         Search indexed code (alias: 's')
  status                 Show currently indexed repo
  help                   Show this help message
  exit                   Exit the REPL
        """
        print(help_text)
