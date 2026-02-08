from pydantic import BaseModel, Field
from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import json

# 1. Definicja struktury odpowiedzi (Structured Output)


class SafetyCheck(BaseModel):
    is_safe: bool = Field(
        description="True if the meal is safe for the user, False otherwise")
    reason: str = Field(
        description="Explanation of why the meal is safe or unsafe")
    alternatives: str = Field(
        description="If unsafe, suggest a quick substitute for the problematic ingredient")

# 2. Klasa Agenta Strażnika


class SafetyAgent(RoutedAgent):
    _delegate: AssistantAgent

    def __init__(self, name: str, forbidden_ingredients: list) -> None:
        super().__init__(name)

        # Konfiguracja klienta z wymuszonym formatem JSON
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}
        )

        # Pobieramy schemat z klasy Pydantic, aby przekazać go w instrukcji
        schema = SafetyCheck.model_json_schema()

        system_msg = f"""
        You are a Food Safety Expert. 
        Analyze recipes for these forbidden ingredients: {', '.join(forbidden_ingredients)}.
        Your final response must be a valid JSON object matching this schema:
        {json.dumps(schema, indent=2)}
        """

        self._delegate = AssistantAgent(
            name=name,
            model_client=model_client,
            system_message=system_msg
        )

    @message_handler
    async def handle_check(self, message: TextMessage, ctx: MessageContext) -> SafetyCheck:
        # Przekazanie wiadomości do wewnętrznego agenta
        response = await self._delegate.on_messages([message], ctx.cancellation_token)
        content = response.chat_message.content

        # Parsowanie odpowiedzi do obiektu Pydantic
        try:
            # Jeśli content jest już słownikiem (zależy od wersji klienta)
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            return SafetyCheck.model_validate(data)
        except Exception as e:
            # Fallback w przypadku błędu parsowania
            return SafetyCheck(
                is_safe=False,
                reason=f"Błąd analizy bezpieczeństwa: {e}",
                alternatives="Skonsultuj się z dietetykiem ręcznie."
            )
