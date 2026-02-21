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

import os
import datetime
import asyncio
import re
import argparse
import time
import logging
from dotenv import load_dotenv
from ollama import AsyncClient
from ddgs import DDGS
from ddgs.http_client import HttpClient
from pocketflow import AsyncNode, AsyncFlow

# Silence ddgs impersonation warnings
HttpClient._impersonates = (None,)
HttpClient._impersonates_os = (None,)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='aiquery.log',
    filemode='a'
)
logger = logging.getLogger("AiQuery")

# Load environment variables
load_dotenv()

class SearchBotBase:
    """Base class for shared tools and client initialization."""
    def __init__(self):
        # Load from .env or use defaults
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1B")
        
        # Initialize the Ollama client
        self.client = AsyncClient(host=self.host)
        
        # Get actual system date for the prompt
        self.today = datetime.datetime.now().strftime("%A, %d %B %Y")

    def clean_snippet(self, text):
        """
        Pre-processes snippets to make them more LLM-friendly, 
        especially for cryptic weather formats.
        """
        # Transform "21.9º" or "25°" into "21.9 graus"
        text = re.sub(r'(\d+(?:\.\d+)?)[\s]?[°º]', r'\1 graus', text)
        # Transform "Min: 20 Max: 30" into more explicit text
        text = re.sub(r'Min:?\s*(\d+)', r'Mínima: \1', text, flags=re.IGNORECASE)
        text = re.sub(r'Max:?\s*(\d+)', r'Máxima: \1', text, flags=re.IGNORECASE)
        return text

    def rank_context(self, search_query, context_list):
        """
        Ranks and filters search results based on relevance to the search query.
        """
        cleaned_list = [self.clean_snippet(snippet) for snippet in context_list]
        
        # General ranking based on search query keywords
        keywords = [word.lower() for word in search_query.split() if len(word) > 2]
        
        def rank_score(text):
            text_lower = text.lower()
            # Keywords are now much more important
            score = sum(10 for k in keywords if k in text_lower)
            
            # Tiny bonus for weather patterns to break ties if search was about weather
            if re.search(r'\d+\s*graus', text_lower):
                score += 1
            return score

        return sorted(cleaned_list, key=rank_score, reverse=True)[:5]

# --- Nodes ---

class BaseAsyncNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    async def post_async(self, shared, prep_res, exec_res):
        return exec_res

class QueryGenNode(BaseAsyncNode):
    async def exec_async(self, shared):
        bot = shared['bot']
        it = shared.get('iteration', 0)
        shared['iteration'] = it + 1
        
        # Include history in query generation to avoid redundancy
        history_summary = "\n".join(shared.get('history', []))[:1000]
        
        prompt = f"""
SYSTEM: You are a search assistant. Convert the user's question into a concise, 
effective search query for DuckDuckGo. 

USER QUESTION: {shared['user_query']}
FOUND SO FAR:
{history_summary if history_summary else "Nothing yet."}

Output ONLY the search query.
SEARCH QUERY:"""
        if it > 0: prompt += f"\nPrevious attempt failed. Try different keywords focusing on: {shared.get('feedback', '')}"
        
        msg = f"[*] Formulating query (Attempt {it+1})..."
        print(msg)
        logger.info(msg)
        
        if 'progress' in shared:
            shared['progress'](0.1 + (it * 0.1), desc=f"Formulating query (Attempt {it+1})...")
            
        try:
            response = await bot.client.generate(model=bot.model, prompt=prompt)
            query = response.get('response', shared['user_query']).strip().strip('"')
            shared['search_query'] = query
            return "default"
        except Exception as e:
            print(f"[!] Query Gen Error: {e}")
            shared['search_query'] = shared['user_query'] # Fallback
            return "default"

class SearchNode(BaseAsyncNode):
    async def exec_async(self, shared):
        bot = shared['bot']
        q = shared['search_query']
        msg = f"[*] Searching for: '{q}'..."
        print(msg)
        logger.info(msg)
        
        if 'progress' in shared:
            shared['progress'](0.3 + (shared.get('iteration', 0) * 0.1), desc=f"Searching for: {q}")
            
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, region='br-pt', max_results=10))

                if not results:
                    # Don't add anything to history if no results
                    return "default"
                
                raw_context = [f"Result: {r.get('title')} - {r.get('body')}" for r in results]
                new_snippets = bot.rank_context(q, raw_context)
                
                # Accumulate history
                if 'history' not in shared: shared['history'] = []
                # Simple deduplication based on text overlap (basic)
                for snip in new_snippets:
                    if snip not in shared['history']:
                        shared['history'].append(snip)
                
                # Update context with everything found so far, ranked by original query
                shared['context'] = "\n".join(bot.rank_context(shared['user_query'], shared['history']))
        except Exception as e:
            print(f"[!] Search Error: {e}")
        return "default"

class RelevanceNode(BaseAsyncNode):
    async def exec_async(self, shared):
        bot = shared['bot']
        context = shared.get('context', 'No info found.')
        prompt = f"""
SYSTEM: You are a relevance checker. Determine if the provided SEARCH RESULTS adequately answer the USER QUESTION.
Reply exactly 'YES' if the context is sufficient, or 'NO' if it is not.

USER QUESTION: {shared['user_query']}
ACCUMULATED SEARCH RESULTS:
{context}

ANSWER (YES/NO):"""
        print(f"[*] Checking relevance of accumulated results...")
        logger.info("Checking relevance of accumulated results...")
        if 'progress' in shared:
            shared['progress'](0.5, desc="Checking relevance of findings...")
            
        try:
            response = await bot.client.generate(model=bot.model, prompt=prompt)
            ans = response.get('response', '').strip().upper()
            
            if "YES" in ans or shared['iteration'] >= 3:
                return "success"
            shared['feedback'] = "Need more specific data or missing parts of the question."
            return "retry"
        except Exception as e:
            print(f"[!] Relevance Check Error: {e}")
            return "success" # Proceed to answer if relevance check fails

class AnswerNode(BaseAsyncNode):
    async def exec_async(self, shared):
        bot = shared['bot']
        # Context is already cumulative and ranked by SearchNode
        safe_context = shared.get('context', '')[:5000]

        prompt = f"""
SYSTEM: Today is {bot.today}. Using the SEARCH RESULTS provided, answer the user's question accurately.
If you don't know the answer, say so based on the results.

SEARCH RESULTS:
{safe_context}

USER QUESTION: {shared['user_query']}
ANSWER (in the same language):"""

        msg = f"[*] Generating answer (Streaming)..."
        print(msg)
        logger.info(msg)
        
        if 'progress' in shared:
            shared['progress'](0.8, desc="Generating final answer...")
            
        try:
            response = await bot.client.generate(
                model=bot.model,
                prompt=prompt,
                stream=True
            )

            full_response = ""
            async for chunk in response:
                content = chunk.get('response', '')
                print(content, end='', flush=True)
                full_response += content
            
            print("\n" + "-"*30)
            shared['answer'] = full_response
            return "default"

        except Exception as e:
            print(f"\n[!] Answer Generation Error: {e}")
            shared['answer'] = f"Could not generate an answer due to an error: {e}"
            return "default"

class ReviewNode(BaseAsyncNode):
    async def exec_async(self, shared):
        bot = shared['bot']
        prompt = f"""
System: You are an AI quality assurance bot. Your task is to review the answer provided by another AI.
Assess if the answer is accurate, direct, and fully addresses the user question based ONLY on the provided context.

SCORING CRITERIA:
- 10: Perfect. Accurate, concise, and directly answers the question.
- 7-9: Good. Correct answer but might have minor fluff or formatting issues.
- 4-6: Mediocre. Partially correct or contains irrelevant info.
- 1-3: Poor. Factually wrong, missing the point, or failing to answer the question.

USER QUESTION: {shared['user_query']}
GENERATED ANSWER: {shared['answer']}

Output ONLY the integer score (1-10).
SCORE:"""
        msg = "[*] Reviewing generated answer..."
        print(msg)
        logger.info(msg)
        
        if 'progress' in shared:
            shared['progress'](0.9, desc="Critiquing answer quality...")
            
        try:
            response = await bot.client.generate(model=bot.model, prompt=prompt)
            match = re.search(r'\d+', response.get('response', '0'))
            score = int(match.group()) if match else 0
            log_score = f"[*] Answer scored: {score}/10"
            print(log_score)
            logger.info(log_score)
            
            if score >= 7 or shared['iteration'] >= 3:
                return "pass"
            shared['feedback'] = "Answer was too vague, incomplete, or inaccurate. Try to find more details."
            return "fail"
        except Exception as e:
            print(f"[!] Review Error: {e}")
            return "pass" # If review fails, assume it's good enough

# --- Flow ---

def build_flow():
    qgen = QueryGenNode()
    search = SearchNode()
    rel = RelevanceNode()
    ans = AnswerNode()
    rev = ReviewNode()

    qgen >> search >> rel
    rel - "success" >> ans
    rel - "retry" >> qgen # If relevance is low, retry query generation
    ans >> rev
    rev - "fail" >> qgen # If answer review fails, retry query generation
    
    flow = AsyncFlow(start=qgen)
    return flow

async def main():
    parser = argparse.ArgumentParser(
        description="AiQuery - Autonomous Search Agent\n\n"
                    "An AI-powered utility that reasons, refines queries, and critques results\n"
                    "to provide accurate answers using local LLMs (Ollama) and DuckDuckGo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  ./aiquery.py \"Qual a capital da França?\"\n"
               "  ./aiquery.py --gui\n"
               "  ./aiquery.py -t \"Como está o clima em SP?\""
    )
    parser.add_argument("query", nargs="?", help="Direct search query (skips interactive prompt)")
    parser.add_argument("-t", "--timestamp", action="store_true", help="Report execution timestamps and duration")
    parser.add_argument("-g", "--gui", action="store_true", help="Launch the Web GUI (Gradio)")
    parser.add_argument("-V", "--version", action="version", version="AiQuery 1.0.0", help="Show current version")
    args = parser.parse_args()

    if args.gui:
        msg = "[*] Launching AiQuery Web GUI..."
        print(msg)
        logger.info(msg)
        from app import launch_gui
        launch_gui()
        return

    bot = SearchBotBase()
    user_query = args.query if args.query else input("Enter your question: ")
    
    if not user_query.strip():
        print("[!] No query provided. Exiting.")
        return

    logger.info(f"Starting query: '{user_query}'")
    shared = {'bot': bot, 'user_query': user_query, 'iteration': 0, 'history': []}
    
    start_time_stamp = datetime.datetime.now()
    start_perf = time.perf_counter()

    try:
        flow = build_flow()
        await flow.run_async(shared)
    except Exception as e:
        logger.error(f"Flow execution failed: {e}")
        print(f"[!] Critical Error: {e}")
    finally:
        end_time_stamp = datetime.datetime.now()
        end_perf = time.perf_counter()
        duration = end_perf - start_perf

        ans = shared.get('answer', 'No answer generated.')
        print(f"\n[FINAL ANSWER]:\n{ans}")
        logger.info("Finished query execution.")

        if args.timestamp:
            timing_info = (
                f"\n{'='*30}\n"
                f"Initial Timestamp: {start_time_stamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Final Timestamp:   {end_time_stamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Elapsed Time:      {duration:.2f} seconds\n"
                f"{'='*30}"
            )
            print(timing_info)
            logger.info(f"Execution time: {duration:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
