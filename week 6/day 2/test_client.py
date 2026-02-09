import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_test():
    # Konfiguracja - upewnij się, że ścieżka do date_server.py jest poprawna
    server_params = StdioServerParameters(
        command="python", args=["date_server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Inicjalizacja jest wymagana!
            await session.initialize()

            # Wywołanie narzędzia
            result = await session.call_tool("get_current_date", arguments={})
            print(f"Wynik z serwera: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run_test())
