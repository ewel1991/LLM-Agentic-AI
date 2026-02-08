from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


class InventoryAgent(RoutedAgent):
    def __init__(self, name: str, inventory_file: str) -> None:
        super().__init__(name)

        # Wczytujemy listę Twoich składników z pliku [cite: 1]
        with open(inventory_file, 'r', encoding='utf-8') as f:
            self.my_inventory = f.read()

        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

        system_msg = f"""
        Jesteś Ekspertem Spiżarni. Twoja lista dostępnych składników to:
        {self.my_inventory}

        Twoim zadaniem jest porównanie propozycji dietetyka z tą listą.
        1. Wskaż, które składniki z przepisu JUŻ MASZ w domu.
        2. Wypisz tylko te brakujące, które muszą trafić na listę zakupów.
        3. Jeśli dietetyk użył czegoś, czego nie masz, a masz bliski zamiennik (np. mąka żytnia zamiast pszennej), zaproponuj zmianę.
        """

        self._delegate = AssistantAgent(
            name=name,
            model_client=model_client,
            system_message=system_msg
        )

    @message_handler
    async def handle_inventory(self, message: TextMessage, ctx: MessageContext) -> TextMessage:
        response = await self._delegate.on_messages([message], ctx.cancellation_token)
        return TextMessage(content=response.chat_message.content, source=self.id.type)
