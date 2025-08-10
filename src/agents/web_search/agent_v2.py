from strands import Agent
from dotenv import load_dotenv
from strands_tools.tavily import (
    tavily_search, tavily_extract, tavily_crawl, tavily_map
)

load_dotenv()

agent = Agent(tools=[tavily_search, tavily_extract, tavily_crawl, tavily_map])
user_input = input('質問を入力：')
agent(user_input)
