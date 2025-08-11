import os
from strands import Agent
from strands.multiagent.a2a import A2AServer
from dotenv import load_dotenv
from tools.web_search import web_search

load_dotenv()
MODEL_ID = os.getenv("BEDROCK_MODEL_ID","")

agent = Agent(tools=[web_search], description="web検索エージェント", model=MODEL_ID,)
server = A2AServer(
    agent=agent, 
    port=9000
)

server.serve()
