"""
Launcher for the refactored paper-crawler.

This small entrypoint keeps backward compatibility: users can still run

    python main.py

and it will call the real entrypoint at `src.main:main()`.
"""

from src.main import main as run_main


if __name__ == '__main__':
    run_main()
