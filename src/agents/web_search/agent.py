from strands import Agent
from dotenv import load_dotenv
from tools.web_search import web_search

load_dotenv()

agent = Agent(tools=[web_search])
user_input = input('質問を入力：')
agent(user_input)
