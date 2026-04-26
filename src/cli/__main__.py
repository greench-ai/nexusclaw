"""NexusClaw CLI entry point — python3 -m nexusclaw"""
import sys
sys.path.insert(0, __file__.rsplit('/', 2)[0] if '/' in __file__ else '.')
from src.cli.main import main
if __name__ == "__main__":
    main()
