from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


class ShoppingAgent(RoutedAgent):
    _delegate: AssistantAgent

    def __init__(self, name: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

        system_msg = """
        Jesteś asystentem zakupowym. 
        Twoim zadaniem jest wyciągnięcie listy produktów z jadłospisu przygotowanego przez dietetyka.
        Przedstaw listę w formie czytelnej tabeli Markdown z kolumnami: Produkt, Ilość, Sekcja (np. Warzywa, Mięso).
        Nie dodawaj zbędnych komentarzy, tylko tabelę.
        """

        self._delegate = AssistantAgent(
            name=name,
            model_client=model_client,
            system_message=system_msg
        )

    @message_handler
    async def handle_shopping(self, message: TextMessage, ctx: MessageContext) -> TextMessage:
        response = await self._delegate.on_messages([message], ctx.cancellation_token)
        return TextMessage(content=response.chat_message.content, source=self.id.type)
