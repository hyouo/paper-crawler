# src/main.py

import argparse
import logging
import sys
import questionary
import copy
from rich.console import Console
from rich.progress import Progress

from . import config
from . import i18n
from .crawler import Crawler
from .database import init_db
from .utils import setup_logging
from .fetchers import get_arxiv_categories, get_biorxiv_categories

logger = logging.getLogger(__name__)
console = Console()

class CliApp:
    """
    Command-line interface application class.
    """

    def __init__(self):
        self.args = None
        self.config_data = None
        self.t = None  # Translation function

    def setup(self):
        """
        Initializes the application, including logging, database, and argument parsing.
        """
        setup_logging()
        logger.info("Initializing database...")
        init_db()
        self.parse_arguments()
        # self.t is now set within parse_arguments
        self.load_configuration()

    def parse_arguments(self):
        """
        Parses command-line arguments with proper i18n support.
        """
        # Pre-parser to find the --lang argument
        pre_parser = argparse.ArgumentParser(add_help=False)
        pre_parser.add_argument("--lang", type=str, default="en", choices=["en", "zh"])
        pre_args, remaining_argv = pre_parser.parse_known_args()

        # Set up the translation function
        self.t = i18n.get_translation(pre_args.lang)
        t = self.t # shorthand

        # Main parser with translated help messages
        parser = argparse.ArgumentParser(description=t['cli_description'])
        parser.add_argument(
            "--config",
            type=str,
            default="config.yaml",
            help=t['cli_config_help'],
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["keyword", "category", "interactive"],
            default="interactive",
            help=t['cli_mode_help'],
        )
        parser.add_argument(
            "--lang",
            type=str,
            default="en",
            choices=["en", "zh"],
            help=t['cli_lang_help'],
        )
        self.args = parser.parse_args(remaining_argv)
        # Update lang in args from the pre-parser, as it might not be in remaining_argv
        self.args.lang = pre_args.lang

    def load_configuration(self):
        """
        Loads the configuration file.
        """
        try:
            self.config_data = config.load_config(self.args.config)
            logger.info(self.t["cli_config_loaded"].format(path=self.args.config))
        except FileNotFoundError as e:
            logger.error(self.t["cli_config_not_found"].format(e=e))
            sys.exit(1)
        except Exception as e:
            logger.error(self.t["cli_config_load_error"].format(e=e))
            sys.exit(1)

    def run(self):
        """
        Runs the fetch task.
        """
        if self.args.mode == 'interactive':
            self.run_interactive_entry()
        else:
            self.run_direct_mode(self.args.mode)

    def run_direct_mode(self, fetch_method, runtime_config=None):
        """
        Runs in direct mode using command-line arguments and config.yaml.
        """
        final_config = self.config_data
        if runtime_config:
            final_config = copy.deepcopy(self.config_data)
            if "categories" in runtime_config:
                final_config["categories"] = runtime_config["categories"]
            if "keywords" in runtime_config:
                final_config["keywords"] = runtime_config["keywords"]

        console.rule(f"[bold blue]{self.t['cli_executing_crawl'].format(method=fetch_method)}[/bold blue]")

        crawler = Crawler(final_config, socketio=None)
        categories_to_fetch = final_config.get("categories", {})
        new_papers = crawler._run_crawl_task(fetch_method, categories_to_fetch)

        if not new_papers:
            logger.info(self.t["cli_no_new_papers"])
        else:
            console.rule(f"[bold blue]{self.t['cli_start_download'].format(count=len(new_papers))}[/bold blue]")
            with Progress(console=console) as progress:
                task = progress.add_task(f"[green]{self.t['cli_downloading']}...", total=len(new_papers))
                for paper in new_papers:
                    logger.info(f"{self.t['cli_downloading_paper'].format(title=paper['title'])}")
                    crawler.download_single_paper(paper)
                    progress.update(task, advance=1)

        logger.info(self.t["cli_all_tasks_complete"])
        console.rule(f"[bold green]{self.t['cli_done']}[/bold green]")

    def run_interactive_entry(self):
        """
        Entry point for interactive mode, letting the user choose quick or preset mode.
        """
        # Prompt for language if not specified via command line
        if '--lang' not in sys.argv and '-h' not in sys.argv and '--help' not in sys.argv:
            lang_choice = questionary.select(
                "Please select a language / 请选择语言:",
                choices=[
                    {"name": "English", "value": "en"},
                    {"name": "中文", "value": "zh"},
                ]
            ).ask()
            if lang_choice is None: # User cancelled
                logger.info("Exiting.")
                return

            if lang_choice != self.args.lang:
                self.args.lang = lang_choice
                self.t = i18n.get_translation(self.args.lang)

        console.rule(f"[bold blue]{self.t['cli_interactive_mode']}[/bold blue]")

        run_mode = questionary.select(
            self.t["cli_welcome"],
            choices=[
                {"name": self.t["cli_quick_mode"], "value": "quick"},
                {"name": self.t["cli_preset_mode"], "value": "preset"},
                {"name": self.t["cli_exit"], "value": "exit"},
            ],
        ).ask()

        if run_mode is None or run_mode == "exit":
            logger.info(self.t["cli_exiting"])
            return

        if run_mode == "quick":
            fetch_method = self.config_data.get("fetch_settings", {}).get("method", "category")
            self.run_direct_mode(fetch_method)
        elif run_mode == "preset":
            self.run_preset_mode()

    def run_preset_mode(self):
        """
        Guides the user through setting up fetching parameters.
        """
        console.print(f"\n[bold green]{self.t['cli_preset_mode_setup']}[/bold green]")

        fetch_method = questionary.select(
            self.t["cli_choose_fetch_mode"],
            choices=[
                {"name": self.t["cli_mode_category"], "value": "category"},
                {"name": self.t["cli_mode_keyword"], "value": "keyword"},
            ],
        ).ask()

        if fetch_method is None: return

        runtime_config = {"categories": {"arxiv": [], "biorxiv": []}, "keywords": []}

        if fetch_method == 'category':
            console.print(f"\n[bold]{self.t['cli_fetching_categories']}[/bold]")
            arxiv_choices = self._format_arxiv_choices()
            biorxiv_choices = self._format_biorxiv_choices()

            console.print(f"{self.t['cli_prompt_select']}")

            selected_arxiv = questionary.checkbox(self.t["cli_select_arxiv"], choices=arxiv_choices).ask()
            if selected_arxiv is None: return

            selected_biorxiv = questionary.checkbox(self.t["cli_select_biorxiv"], choices=biorxiv_choices).ask()
            if selected_biorxiv is None: return

            runtime_config["categories"]["arxiv"] = selected_arxiv
            runtime_config["categories"]["biorxiv"] = selected_biorxiv

        elif fetch_method == 'keyword':
            console.print(f"\n[bold]{self.t['cli_enter_keywords']}[/bold]")
            keywords = questionary.multiline(
                f"{self.t['cli_keywords_prompt']}",
                marker=">",
                validate=lambda text: True if len(text.strip()) > 0 else self.t["cli_keywords_validate"]
            ).ask()
            if keywords is None: return
            runtime_config["keywords"] = [kw.strip() for kw in keywords.strip().split('\n')]

        console.print(f"\n[bold blue]{self.t['cli_run_config']}[/bold blue]")
        console.print(runtime_config)

        if questionary.confirm(f"{self.t['cli_confirm_proceed']}").ask():
            self.run_direct_mode(fetch_method, runtime_config)
        else:
            logger.info(self.t["cli_crawl_cancelled"])

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
