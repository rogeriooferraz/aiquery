#!/usr/bin/env python3

# MIT License

# Copyright (c) 2026 Rogerio O. Ferraz

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gradio as gr
import asyncio
from aiquery import SearchBotBase, build_flow

async def run_agent(question, progress=gr.Progress()):
    """Bridge between Gradio and the AiQuery Agent."""
    progress(0, desc="Initializing AiQuery...")
    bot = SearchBotBase()
    
    # Initialize shared state
    shared = {
        'bot': bot, 
        'user_query': question, 
        'iteration': 0, 
        'history': [],
        'progress': progress  # Pass progress object for real-time updates
    }
    
    flow = build_flow()
    
    # Run the flow - internal nodes will update the progress bar
    await flow.run_async(shared)
    
    progress(1.0, desc="Finalizing answer...")
    return shared.get('answer', "No answer generated.")

async def chat_interface(question):
    """Async handler for the AiQuery agent."""
    if not question.strip():
        return "Please enter a question."
    return await run_agent(question)

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# 🔍 AiQuery")
    gr.Markdown("An autonomous search agent that reasons, refines queries, and critiques results.")
    
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                lines=3, 
                placeholder="Ex: Who won the Best Picture Oscar in 2024?", 
                label="Your Question"
            )
            submit_btn = gr.Button("Submit", variant="primary")
            
        with gr.Column():
            output_md = gr.Markdown(label="AiQuery Analysis")

    gr.Examples(
        examples=[
            ["Qual a capital da França?"],
            ["Quem ganhou o Oscar de Melhor Filme em 2024?"],
            ["Compare o clima de Londres e Paris hoje."]
        ],
        inputs=input_text
    )

    submit_btn.click(
        fn=chat_interface,
        inputs=input_text,
        outputs=output_md,
        show_progress="full"
    )

def launch_gui():
    """Launches the AiQuery Gradio interface."""
    demo.launch(theme="soft")
    # demo.launch(theme="soft", app_title="AiQuery")

if __name__ == "__main__":
    launch_gui()
