"""CLI entry point for the AI architectural take-off agent."""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent import TakeoffAgent
from .reporters.excel_reporter import ExcelReporter

console = Console()


def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def _confidence_color(conf: str) -> str:
    return {"high": "green", "medium": "yellow", "low": "red"}.get(conf.lower(), "white")


def _print_result(result, show_notes: bool = True):
    console.print(
        f"\n  Drawing type:  [cyan]{result.drawing_type.replace('_', ' ').title()}[/cyan]"
    )
    console.print(f"  Scale:         [cyan]{result.scale}[/cyan]")
    tb = result.title_block or {}
    if tb.get("project_name"):
        console.print(f"  Project:       [cyan]{tb['project_name']}[/cyan]")
    if tb.get("drawing_number"):
        console.print(f"  Drawing No.:   [cyan]{tb['drawing_number']}[/cyan]")

    conf = result.overall_confidence
    col = _confidence_color(conf)
    console.print(f"  Confidence:    [{col}]{conf.upper()}[/{col}]")
    console.print(f"  Line items:    [cyan]{len(result.line_items)}[/cyan]")

    if result.line_items:
        table = Table(title="\nTake-Off", show_lines=True, highlight=True)
        table.add_column("#", style="dim", width=4, no_wrap=True)
        table.add_column("Category", style="bold", width=18)
        table.add_column("Code", width=10)
        table.add_column("Description", width=38)
        table.add_column("Qty", justify="right", width=9)
        table.add_column("Unit", width=6)
        table.add_column("Conf", width=8)

        for i, item in enumerate(result.line_items, 1):
            qty = item.get("quantity", 0)
            qty_str = f"{qty:,.1f}" if isinstance(qty, float) and qty != int(qty) else f"{int(qty):,}"
            conf_i = (item.get("confidence") or "medium").lower()
            col_i = _confidence_color(conf_i)
            table.add_row(
                str(i),
                item.get("category", ""),
                item.get("item_code", "") or "",
                item.get("description", ""),
                qty_str,
                item.get("unit", ""),
                f"[{col_i}]{conf_i.upper()}[/{col_i}]",
            )
        console.print(table)

    if result.verification_items:
        console.print("\n[bold yellow]⚠  Items requiring field verification:[/bold yellow]")
        for vi in result.verification_items:
            console.print(f"  • {vi}")

    if show_notes and result.estimator_notes:
        console.print(f"\n[bold]Estimator notes:[/bold]\n{result.estimator_notes}")


# ── Commands ──────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """AI-powered architectural take-off agent.

    Analyses partition plans and reflected ceiling plans (RCPs) using Claude AI
    and exports structured take-off reports to Excel.
    """


@cli.command()
@click.argument("drawing", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output", "-o",
    default=None,
    help="Output Excel file path (default: <drawing>_takeoff.xlsx)",
)
@click.option(
    "--model", "-m",
    default="claude-sonnet-4-6",
    show_default=True,
    help="Claude model to use",
)
@click.option("--no-enhance", is_flag=True, help="Skip image contrast/sharpness enhancement")
@click.option("--no-excel", is_flag=True, help="Print results only, skip Excel export")
@click.option("--verbose", "-v", is_flag=True, help="Verbose debug logging")
def analyze(drawing, output, model, no_enhance, no_excel, verbose):
    """Analyse a single architectural drawing and produce a take-off.

    DRAWING can be a PDF, PNG, JPG, TIFF, or other image file.
    """
    _setup_logging(verbose)
    drawing_path = Path(drawing)

    if output is None:
        output = drawing_path.parent / f"{drawing_path.stem}_takeoff.xlsx"
    output = Path(output)

    console.print(
        Panel(
            f"[bold]Drawing:[/bold]  [green]{drawing_path.name}[/green]\n"
            f"[bold]Model:[/bold]    [cyan]{model}[/cyan]",
            title="[bold blue]AI Architectural Take-Off Agent[/bold blue]",
            expand=False,
        )
    )

    with console.status("[bold green]Analysing drawing…[/bold green]", spinner="dots"):
        try:
            agent = TakeoffAgent(model=model)
            result = agent.analyze_drawing(
                drawing_path, verbose=verbose, enhance_image=not no_enhance
            )
        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Analysis failed:[/red] {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    console.print("[bold green]✓ Analysis complete[/bold green]")
    _print_result(result)

    if not no_excel:
        try:
            reporter = ExcelReporter()
            reporter.generate(result, output)
            console.print(f"\n[bold green]✓ Excel report:[/bold green] [blue]{output}[/blue]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not write Excel report: {e}")


@cli.command()
@click.argument("drawings", nargs=-1, type=click.Path(exists=True, dir_okay=False), required=True)
@click.option(
    "--output-dir", "-o",
    default=".",
    show_default=True,
    help="Directory for Excel output files",
)
@click.option("--model", "-m", default="claude-sonnet-4-6", show_default=True)
@click.option("--no-enhance", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def batch(drawings, output_dir, model, no_enhance, verbose):
    """Analyse multiple drawings and export a take-off Excel for each.

    Example:
        takeoff batch floor_plan.pdf rcp.pdf --output-dir ./takeoffs/
    """
    _setup_logging(verbose)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    agent = TakeoffAgent(model=model)
    reporter = ExcelReporter()

    total = len(drawings)
    ok = 0

    for idx, drawing in enumerate(drawings, 1):
        path = Path(drawing)
        console.print(f"\n[bold]({idx}/{total})[/bold] {path.name}")
        with console.status(f"  Analysing…", spinner="dots"):
            try:
                result = agent.analyze_drawing(path, verbose=verbose, enhance_image=not no_enhance)
                out = out_dir / f"{path.stem}_takeoff.xlsx"
                reporter.generate(result, out)
                console.print(
                    f"  [green]✓[/green] {len(result.line_items)} items  →  {out.name}  "
                    f"[{_confidence_color(result.overall_confidence)}]{result.overall_confidence.upper()}[/{_confidence_color(result.overall_confidence)}]"
                )
                ok += 1
            except Exception as e:
                console.print(f"  [red]✗ Failed:[/red] {e}")

    console.print(f"\n[bold]Done — {ok}/{total} drawing(s) processed[/bold]")


@cli.command("drawing-set")
@click.argument("pdf", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output-dir", "-o",
    default=".",
    show_default=True,
    help="Directory for Excel output files",
)
@click.option("--model", "-m", default="claude-sonnet-4-6", show_default=True)
@click.option("--no-enhance", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
def drawing_set(pdf, output_dir, model, no_enhance, verbose):
    """Analyse every page of a multi-page PDF drawing set.

    Produces one Excel take-off file per page.

    Example:
        takeoff drawing-set full_set.pdf --output-dir ./takeoffs/
    """
    _setup_logging(verbose)
    pdf_path = Path(pdf)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel(
            f"[bold]PDF:[/bold]    [green]{pdf_path.name}[/green]\n"
            f"[bold]Model:[/bold] [cyan]{model}[/cyan]",
            title="[bold blue]Drawing Set Take-Off[/bold blue]",
            expand=False,
        )
    )

    with console.status("[bold green]Processing drawing set…[/bold green]", spinner="dots"):
        try:
            agent = TakeoffAgent(model=model)
            results = agent.analyze_drawing_set(
                pdf_path, verbose=verbose, enhance_image=not no_enhance
            )
        except Exception as e:
            console.print(f"[red]Failed:[/red] {e}")
            sys.exit(1)

    reporter = ExcelReporter()
    for i, result in enumerate(results, 1):
        out = out_dir / f"{pdf_path.stem}_page{i:02d}_takeoff.xlsx"
        reporter.generate(result, out)
        console.print(
            f"  Page {i:02d}  {result.drawing_type.replace('_', ' ').title():30s}  "
            f"{len(result.line_items)} items  →  {out.name}"
        )

    console.print(f"\n[bold green]✓ {len(results)} page(s) processed[/bold green]")


def main():
    cli()


if __name__ == "__main__":
    main()
