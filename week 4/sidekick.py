import uuid
from datetime import datetime
from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sidekick_tools import playwright_tools, other_tools


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback for the assistant")
    success_criteria_met: bool = Field(
        description="Is the task done correctly?")
    user_input_needed: bool = Field(
        description="Does the agent need user help?")


class Sidekick:
    def __init__(self):
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        p_tools, self.browser, self.playwright = await playwright_tools()
        o_tools = await other_tools()
        self.tools = p_tools + o_tools

        self.worker_llm = ChatOpenAI(
            model="gpt-4o-mini").bind_tools(self.tools)
        self.evaluator_llm = ChatOpenAI(
            model="gpt-4o-mini").with_structured_output(EvaluatorOutput)
        self.build_graph()

    def worker(self, state: State):
        sys_msg = f"""You are a Travel Planner. Use tools to find ACTUAL data.
        Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Criteria: {state['success_criteria']}
        
        If you get feedback that your plan was rejected, adjust and try again.
        Feedback: {state.get('feedback_on_work', 'None')}"""

        messages = [SystemMessage(content=sys_msg)] + state["messages"]
        return {"messages": [self.worker_llm.invoke(messages)]}

    def evaluator(self, state: State):
        last_ai_msg = state["messages"][-1].content
        history = "\n".join(
            [f"{m.type}: {m.content}" for m in state["messages"][-5:]])

        eval_prompt = f"""Evaluate if this travel plan meets: {state['success_criteria']}
        History: {history}
        Latest Answer: {last_ai_msg}
        Be strict about budget and dates!"""

        res = self.evaluator_llm.invoke([SystemMessage(
            content="You are a strict travel supervisor."), HumanMessage(content=eval_prompt)])
        return {
            "feedback_on_work": res.feedback,
            "success_criteria_met": res.success_criteria_met,
            "user_input_needed": res.user_input_needed,
            "messages": [AIMessage(content=f"Evaluator: {res.feedback}")]
        }

    def worker_router(self, state: State):
        if state["messages"][-1].tool_calls:
            return "tools"
        return "evaluator"

    def eval_router(self, state: State):
        if state["success_criteria_met"] or state["user_input_needed"]:
            return END
        return "worker"

    def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("worker", self.worker)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_node("evaluator", self.evaluator)

        builder.add_edge(START, "worker")
        builder.add_conditional_edges("worker", self.worker_router, {
                                      "tools": "tools", "evaluator": "evaluator"})
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges("evaluator", self.eval_router, {
                                      "worker": "worker", END: END})

        self.graph = builder.compile(checkpointer=self.memory)

    async def run(self, user_msg, criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        # Przygotowujemy stan wejściowy
        input_state = {
            "messages": [HumanMessage(content=user_msg)],
            "success_criteria": criteria
        }

        # Uruchamiamy graf
        result = await self.graph.ainvoke(input_state, config=config)

        # Pobieramy ostatnie odpowiedzi (zazwyczaj Worker + Evaluator)
        # Formatuje to jako listę słowników dla Gradio
        new_messages = []
        for msg in result["messages"]:
            if isinstance(msg, HumanMessage):
                new_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                # Pomijamy puste wiadomości wywołania narzędzi, bierzemy tylko tekst
                if msg.content:
                    new_messages.append(
                        {"role": "assistant", "content": msg.content})

        return new_messages

    def cleanup(self):
        if self.browser:
            asyncio.run(self.browser.close())
