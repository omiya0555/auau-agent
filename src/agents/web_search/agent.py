from strands import Agent
from strands.multiagent.a2a import A2AServer
from dotenv import load_dotenv
from tools.web_search import web_search
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load system prompt from file
def load_system_prompt():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "system_prompt.txt")
    if not os.path.exists(prompt_path):
        logger.warning(f"System prompt file not found: {prompt_path}")
        return "You are a helpful assistant."
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

agent = Agent(
    tools=[web_search],
    description="web検索エージェント",
    system_prompt=load_system_prompt(),
)
server = A2AServer(
    agent=agent, 
    port=9000,
)

server.serve()
