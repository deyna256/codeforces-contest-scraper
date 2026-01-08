"""CLI interface for codeforces-editorial-finder."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from codeforces_editorial.orchestrator import EditorialOrchestrator
from codeforces_editorial.utils.exceptions import CodeforcesEditorialError
from codeforces_editorial.utils.logger import setup_logger

console = Console()


@click.command()
@click.argument("url", required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Ignore cache and force fresh fetch",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Clear cache before running",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--api-key",
    type=str,
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
def main(
    url: str,
    output: Optional[str],
    no_cache: bool,
    clear_cache: bool,
    verbose: bool,
    api_key: Optional[str],
) -> None:
    """
    Extract editorial/tutorial for a Codeforces problem.

    URL should be a Codeforces problem URL, e.g.:
    https://codeforces.com/contest/1234/problem/A
    """
    # Setup logging
    setup_logger(verbose=verbose)

    # Set API key if provided
    if api_key:
        import os

        os.environ["OPENAI_API_KEY"] = api_key

    try:
        with EditorialOrchestrator(use_cache=not no_cache) as orchestrator:
            # Clear cache if requested
            if clear_cache:
                console.print("[yellow]Clearing cache...[/yellow]")
                orchestrator.clear_cache()
                if not url:  # If only clearing cache
                    console.print("[green]Cache cleared successfully[/green]")
                    return

            # Show progress
            console.print(f"[cyan]Fetching editorial for:[/cyan] {url}")

            # Get editorial
            markdown = orchestrator.get_editorial_markdown(url)

            # Output
            if output:
                output_path = Path(output)
                output_path.write_text(markdown, encoding="utf-8")
                console.print(f"[green]Editorial saved to:[/green] {output_path}")
            else:
                # Display to console with rich formatting
                console.print("\n")
                console.print(
                    Panel(
                        Markdown(markdown),
                        title="[bold cyan]Editorial[/bold cyan]",
                        border_style="cyan",
                    )
                )

    except CodeforcesEditorialError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
