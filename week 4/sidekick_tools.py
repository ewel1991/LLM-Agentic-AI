import os
import requests
import asyncio
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit, FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import Tool
from dotenv import load_dotenv

load_dotenv(override=True)


async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Sends a push notification via Pushover"""
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER"),
        "message": text
    }
    requests.post(url, data=data)
    return "Notification sent successfully"


def get_file_tools():
    if not os.path.exists("sandbox"):
        os.makedirs("sandbox")
    return FileManagementToolkit(root_dir="sandbox").get_tools()


async def other_tools():
    serper = GoogleSerperAPIWrapper()
    search_tool = Tool(
        name="search",
        func=serper.run,
        description="Search the web for real-time info on flights, hotels, and prices."
    )

    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Send a notification to the user when a plan is ready."
    )

    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_repl = PythonREPLTool()

    return get_file_tools() + [push_tool, search_tool, python_repl, wiki]
