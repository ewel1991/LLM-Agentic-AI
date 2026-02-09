import asyncio
import json
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(override=True)

# Parametry serwera SQLite z Twojego marketplace'u
# Musimy podać ścieżkę do pliku bazy danych
db_path = "moje_dane.db"
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-sqlite", "--db", db_path]
)


async def run_sqlite_mcp_task():
    client = OpenAI()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Pobieramy listę narzędzi (np. query, create_table)
            mcp_tools = await session.list_tools()

            # 2. Mapujemy na format OpenAI (z dodatkiem additionalProperties: False)
            # Pamiętasz ten detal z accounts_client.py? Jest kluczowy!
            openai_tools = []
            for tool in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {**tool.inputSchema, "additionalProperties": False}
                    }
                })

            # 3. Zadanie dla Agenta
            messages = [{
                "role": "user",
                "content": "Stwórz tabelę 'products' z kolumnami 'name' i 'price'. Dodaj tam Apple (3.5) i Banana (1.2), a potem podaj sumę ich cen."
            }]

            # Tutaj następuje pętla konwersacji (analogiczna do tej z Twojego materiału o Fetch)
            # Agent będzie musiał wywołać narzędzie 'query' lub 'write_query'

            # ... (tutaj obsługa response i call_tool jak w poprzednim ćwiczeniu)
            print("Serwer połączony, narzędzia pobrane. Czekam na instrukcje...")

if __name__ == "__main__":
    asyncio.run(run_sqlite_mcp_task())
