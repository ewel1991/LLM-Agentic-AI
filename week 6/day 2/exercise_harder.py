import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv(override=True)

# Ustawienia serwera (tak jak w Twoich materiałach)
server_params = StdioServerParameters(
    command="python", args=["date_server.py"])


async def run_native_mcp_client():
    client = OpenAI()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Pobierz narzędzia z serwera MCP
            mcp_tools = await session.list_tools()

            # 2. Przekonwertuj narzędzie MCP na format OpenAI
            # (To jest ta trudniejsza część z accounts_client.py)
            tools_for_openai = []
            for tool in mcp_tools.tools:
                tools_for_openai.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # 3. Pierwsze zapytanie do OpenAI
            messages = [
                {"role": "user", "content": "Jaka jest dzisiejsza data?"}]

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools_for_openai
            )

            # 4. Obsłuż Tool Call (Logika agenta ręcznie!)
            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call:
                # Wywołaj serwer MCP
                mcp_result = await session.call_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )

                # Wyślij wynik z powrotem do OpenAI
                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": mcp_result.content[0].text
                })

                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                print(
                    f"Finalny wynik: {final_response.choices[0].message.content}")

if __name__ == "__main__":
    asyncio.run(run_native_mcp_client())
