# src/main.py

import argparse
import logging
import sys
import questionary
import copy
from rich.console import Console
from rich.progress import Progress

from . import config
from .crawler import Crawler
from .database import init_db
from .utils import setup_logging
from .fetchers import get_arxiv_categories, get_biorxiv_categories

logger = logging.getLogger(__name__)
console = Console()

class CliApp:
    """
    命令行界面应用程序类。
    """

    def __init__(self):
        self.args = None
        self.config_data = None

    def setup(self):
        """
        初始化应用程序，包括日志、数据库和参数解析。
        """
        setup_logging()
        logger.info("Initializing database...")
        init_db()
        self.parse_arguments()
        self.load_configuration()

    def parse_arguments(self):
        """
        解析命令行参数。
        """
        parser = argparse.ArgumentParser(description="A command-line tool for fetching scientific papers.")
        parser.add_argument(
            "--config",
            type=str,
            default="config.yaml",
            help="Path to the configuration file.",
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["keyword", "category", "interactive"],
            default="interactive", # Default to interactive if no mode is specified
            help="Set the fetch mode. 'interactive' will start a guided session.",
        )
        self.args = parser.parse_args()

    def load_configuration(self):
        """
        加载配置文件。
        """
        try:
            self.config_data = config.load_config(self.args.config)
            logger.info(f"Configuration loaded from '{self.args.config}'.")
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

    def run(self):
        """
        运行抓取任务。
        """
        if self.args.mode == 'interactive':
            self.run_interactive_entry()
        else:
            self.run_direct_mode(self.args.mode)

    def run_direct_mode(self, fetch_method, runtime_config=None):
        """
        以直接模式运行，使用命令行参数和 config.yaml。
        """
        final_config = self.config_data
        if runtime_config:
            # Deep copy to avoid modifying the base config object
            final_config = copy.deepcopy(self.config_data)
            # Merge runtime settings
            if "categories" in runtime_config:
                final_config["categories"] = runtime_config["categories"]
            if "keywords" in runtime_config:
                final_config["keywords"] = runtime_config["keywords"]

        console.rule(f"[bold blue]Executing Crawl: {fetch_method}[/bold blue]")

        crawler = Crawler(final_config, socketio=None)

        # The categories to fetch are now derived from the final_config
        categories_to_fetch = final_config.get("categories", {})

        new_papers = crawler._run_crawl_task(fetch_method, categories_to_fetch)

        if not new_papers:
            logger.info("没有找到需要下载的新论文。")
        else:
            console.rule(f"[bold blue]开始下载 {len(new_papers)} 篇新论文[/bold blue]")
            with Progress(console=console) as progress:
                task = progress.add_task("[green]下载中...", total=len(new_papers))
                for paper in new_papers:
                    logger.info(f"正在下载: {paper['title']}")
                    # Note: _download_paper is now private. We use the public method.
                    # The public method handles DB interaction and notifications (which are suppressed w/o socketio).
                    crawler.download_single_paper(paper)
                    progress.update(task, advance=1)

        logger.info("所有任务完成。")
        console.rule("[bold green]Done[/bold green]")

    def run_interactive_entry(self):
        """
        交互模式的入口点，让用户选择快速模式或预设模式。
        """
        console.rule("[bold blue]Interactive Mode[/bold blue]")

        run_mode = questionary.select(
            "Welcome! How would you like to run the crawler?",
            choices=[
                {"name": "Quick Mode - Use settings from config.yaml", "value": "quick"},
                {"name": "Preset Mode - Interactively choose settings for this run", "value": "preset"},
                {"name": "Exit", "value": "exit"},
            ],
        ).ask()

        if run_mode is None or run_mode == "exit":
            logger.info("Exiting.")
            return

        if run_mode == "quick":
            fetch_method = self.config_data.get("fetch_settings", {}).get("method", "category")
            self.run_direct_mode(fetch_method)
        elif run_mode == "preset":
            self.run_preset_mode()

    def run_preset_mode(self):
        """
        引导用户完成抓取参数的设置。
        """
        console.print("\n[bold green]Starting Preset Mode Setup...[/bold green]")

        fetch_method = questionary.select(
            "First, choose a fetch mode:",
            choices=[
                {"name": "Category - Fetch papers from specific scientific categories", "value": "category"},
                {"name": "Keyword - Fetch papers using a list of keywords", "value": "keyword"},
            ],
        ).ask()

        if fetch_method is None: return

        runtime_config = {"categories": {"arxiv": [], "biorxiv": []}, "keywords": []}

        if fetch_method == 'category':
            console.print("\n[bold]Fetching available categories...[/bold]")
            arxiv_choices = self._format_arxiv_choices()
            biorxiv_choices = self._format_biorxiv_choices()

            console.print("Use [bold]spacebar[/bold] to select/deselect, [bold]enter[/bold] to confirm.")

            selected_arxiv = questionary.checkbox("Select arXiv categories:", choices=arxiv_choices).ask()
            if selected_arxiv is None: return

            selected_biorxiv = questionary.checkbox("Select bioRxiv categories:", choices=biorxiv_choices).ask()
            if selected_biorxiv is None: return

            runtime_config["categories"]["arxiv"] = selected_arxiv
            runtime_config["categories"]["biorxiv"] = selected_biorxiv

        elif fetch_method == 'keyword':
            console.print("\n[bold]Enter keywords, one per line. Press ESC followed by Enter when done.[/bold]")
            keywords = questionary.multiline(
                "Keywords:",
                marker=">",
                validate=lambda text: True if len(text.strip()) > 0 else "Please enter at least one keyword."
            ).ask()
            if keywords is None: return
            runtime_config["keywords"] = [kw.strip() for kw in keywords.strip().split('\n')]

        console.print("\n[bold blue]Configuration for this run:[/bold blue]")
        console.print(runtime_config)

        if questionary.confirm("Proceed with crawling?").ask():
            self.run_direct_mode(fetch_method, runtime_config)
        else:
            logger.info("Crawl cancelled by user.")

    def _format_arxiv_choices(self):
        """Formats arXiv categories for questionary."""
        choices = []
        for group in get_arxiv_categories():
            choices.append(questionary.Separator(f'--- {group["group"]} ---'))
            for cat in group["categories"]:
                choices.append({"name": f"{cat['name']} ({cat['code']})", "value": cat['code']})
        return choices

    def _format_biorxiv_choices(self):
        """Formats bioRxiv categories for questionary."""
        return [{"name": cat, "value": cat} for cat in get_biorxiv_categories()]


def main():
    """
    主函数，程序的命令行入口点。
    """
    cli_app = CliApp()
    cli_app.setup()
    cli_app.run()

if __name__ == "__main__":
    main()
