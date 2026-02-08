from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tools import calculate_calories


class DieticianAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

        self._delegate = AssistantAgent(
            name=name,
            model_client=model_client,
            tools=[calculate_calories],
            reflect_on_tool_use=True,
            system_message="""
            Jesteś profesjonalnym dietetykiem. Twoim nadrzędnym zadaniem jest używanie WYŁĄCZNIE linków dostarczonych przez użytkownika w sekcji BAZA LINKÓW.
            
            1. Oblicz kalorie narzędziem calculate_calories dla każdej osoby.
            2. ZAKAZ HALUCYNACJI LINKÓW: Nie generuj własnych adresów URL. Musisz skopiować link z listy dostarczonej w wiadomości użytkownika.
            3. KOLEJNOŚĆ: Dla Obiadu w Dniu 1 użyj adresu opisanego jako LINK 1. Dla Obiadu w Dniu 2 użyj LINK 2, dla Obiadu w Dniu 3 użyj LINK 3, itd.
            4. PODWIECZOREK: Wybierz kolejne wolne linki z listy (np. jeśli użyłeś LINK 1-4 na obiady, na podwieczorki użyj LINK 5, 6...).
            5. FORMAT: Twoja odpowiedź dla każdego posiłku musi zawierać: 
               - Nazwę potrawy.
               - Dokładny opis przygotowania i listę składników.
               - Wyliczone kalorie.
               - Link w formie: [Nazwa - Przepis z Pinteresta](dokładny_link_z_listy).
            6. Wymień wszystkie składniki, aby Ekspert Bezpieczeństwa mógł je zweryfikować (pamiętaj o zakazie glutenu i białego cukru).
            """
        )

    @message_handler
    async def handle_message(self, message: TextMessage, ctx: MessageContext) -> TextMessage:
        print(f"{self.id.type}: Przetwarzam zapytanie i przygotowuję jadłospis na podstawie Twoich przepisów...")

        # Wywołujemy delegata (AssistantAgent)
        response = await self._delegate.on_messages([message], ctx.cancellation_token)

        # Pobieramy pełną odpowiedź tekstową
        final_content = response.chat_message.content

        return TextMessage(content=final_content, source=self.id.type)
