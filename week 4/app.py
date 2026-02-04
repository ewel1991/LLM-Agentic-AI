import gradio as gr
import asyncio
from sidekick import Sidekick


async def chat_fn(msg, criteria, history):
    if not history:
        history = []
    # Tworzymy nową instancję sidekicka dla sesji, jeśli jej nie ma
    sk = Sidekick()
    await sk.setup()
    new_history = await sk.run(msg, criteria, history)
    return "", "", new_history

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ✈️ AI Sidekick: Travel Planner")
    criteria_input = gr.Textbox(
        label="Success Criteria", placeholder="e.g. Budget < 2000 PLN, Hotel > 8.0, Flights included")
    chatbot = gr.Chatbot(label="Travel Plan")
    msg_input = gr.Textbox(label="Where do you want to go?")
    btn = gr.Button("Plan Trip")

    btn.click(chat_fn, [msg_input, criteria_input, chatbot], [
              msg_input, criteria_input, chatbot])

if __name__ == "__main__":
    demo.launch()
