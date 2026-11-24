import readline  # noqa: F401  (line editing + ↑/↓ history for input())
from typing import Callable, List
import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

from src.openai_llm import get_llm
from src.validators import MinimalSource
from src.var import MAX_TOKENS, SYSTEM, answer_prompt

Retriever = Callable[[str, int, bool, bool], List[MinimalSource]]

LOGO = r"""
 ____      _      ____
|  _ \    / \    / ___|
| |_) |  / _ \  | |  _
|  _ <  / ___ \ | |_| |
|_| \_\/_/   \_\ \____|
"""
EXIT = {"/quit", "/exit", "quit", "exit"}
PROMPT = "\001\033[1;36m\002❯\001\033[0m\002 "


def banner(console: Console, method: str, reranker: bool, model: str) -> None:
    """Logo on the left, what is running on the right."""
    logo = LOGO.strip("\n").splitlines()
    info = [
        "", "[bold]Ask the vLLM docs[/]",
        f"[dim]{method}{' · reranker' if reranker else ''} · {model}[/]",
        "", "[dim]/quit to exit[/]",
    ]
    for art, side in zip(logo, info):
        console.print(f"[bold cyan]{art:<26}[/]{side}")
    console.print()


def sources_line(sources: List[MinimalSource]) -> Text:
    """' Sources  1. a.md' then aligned lines, file paths only, deduped."""
    paths = list(dict.fromkeys(s.file_path for s in sources))
    if not paths:
        return Text(" No sources found\n", style="dim")
    text = Text()
    for i, path in enumerate(paths, 1):
        label = " Sources  " if i == 1 else " " * 10
        text.append(label, style="bold").append(f"{i}. {path}\n", "dim")
    return text


def ask(
    console: Console, retrieve: Retriever, query: str,
    k: int, keep: int, reranker: bool, rewrite: bool,
) -> None:
    """One stateless question: retrieve, stream the answer, list sources."""
    with console.status("[cyan]Searching the documentation…"):
        sources = retrieve(query, k, reranker, rewrite)[:keep]
    prompt = answer_prompt(query, [s.content for s in sources])
    answer = ""
    panel = Panel("", title="Answer", title_align="left",
                  border_style="cyan")
    with Live(panel, console=console, refresh_per_second=8) as live:
        for delta in get_llm().chat_stream(SYSTEM, prompt, MAX_TOKENS):
            answer += delta
            time.sleep(0.01)
            panel.renderable = Markdown(answer)
            live.update(panel)
    console.print(sources_line(sources))
    console.rule(style="dim")


def run_demo(
    retrieve: Retriever, method: str, k: int, keep: int,
    reranker: bool, rewrite: bool,
) -> None:
    """Question → answer loop. No history is ever sent to the model."""
    console = Console()
    banner(console, method, reranker, get_llm().model)
    while True:
        try:
            query = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in EXIT:
            break
        if not query:
            continue
        try:
            ask(console, retrieve, query, k, keep, reranker, rewrite)
        except KeyboardInterrupt:
            console.print("[yellow]Interrupted.[/]")
        except Exception as e:
            console.print(
                f"[red]✗ {e.__class__.__name__}:[/] {escape(str(e))}"
            )
    console.print("\n[dim]Bye![/]")
