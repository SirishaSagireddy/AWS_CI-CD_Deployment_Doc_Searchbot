import os
from pathlib import Path
import logging

list_of_files = [
    "src/__init__.py",
    "src/helper.py",
    "src/prompt.py",
    ".env",
    "setup.py",
    "requirements.txt",
    "research/trials.ipynb",
    "app.py",
    "store_index.py",
    "static/style.css",
    "templates/chat.html",
    "model/instructions.txt"
]

logger_path = "code_logger.log"
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(lineno)s %(message)s',
                    handlers= [logging.FileHandler(logger_path),
                               logging.StreamHandler()])
logger=logging.getLogger(__name__)

for file in list_of_files:
    file_path = Path(file)
    file_exists = file_path.exists()
    file_is_dir = str(file_path.parent) != '.'
    if file_is_dir and not file_exists:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        logger.info(f'Path:{file_path}, Created directory:{file_path.parent} and empty file:{file_path.name}')
    else:
        if not file_exists:
            file_path.touch()
            logger.info(f"Path:{file_path} Created empty file:{file_path.name}")
        else:
            logger.info(f'Path:{file_path} already exists')
    