from dotenv import set_key, load_dotenv
from pathlib import Path

env_path = Path(".") / ".env"
env_path.touch(exist_ok=True)  # ensure file exists
load_dotenv(env_path)          # optional
set_key(str(env_path), "TAVILY_API_KEY", "your_key_here")