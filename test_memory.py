import pytest
import asyncio
from unittest.mock import MagicMock
from aiquery import QueryGenNode, SearchNode, RelevanceNode, AnswerNode

@pytest.mark.asyncio
async def test_memory_accumulation_loop():
    # Mock bot and client
    mock_bot = MagicMock()
    mock_bot.model = "test-model"
    
    # helper for side_effect
    async def mock_gen(*args, **kwargs):
        return mock_gen.results.pop(0)
    mock_gen.results = [
        {"response": "search_query_a"}, # QueryGen 1
        {"response": "NO"},             # Relevance 1
        {"response": "search_query_b"}, # QueryGen 2
        {"response": "YES"},            # Relevance 2
    ]
    mock_bot.client.generate = mock_gen
    
    # Mock search results
    # SearchNode calls rank_context
    def mock_rank(query, context):
        return context[:1] # Just return first result for simplicity
        
    mock_bot.rank_context.side_effect = mock_rank

    # We need to mock DDGS in SearchNode
    with patch('aiquery.DDGS') as mock_ddgs:
        instance = mock_ddgs.return_value.__enter__.return_value
        # First call to DDGS().text returns Result A
        # Second call returns Result B
        instance.text.side_effect = [
            [{"title": "Title A", "body": "Body A"}],
            [{"title": "Title B", "body": "Body B"}]
        ]

        shared = {
            'bot': mock_bot,
            'user_query': "Compare A and B",
            'iteration': 0,
            'history': []
        }

        # Step 1: QueryGen
        qgen = QueryGenNode()
        await qgen.exec_async(shared)
        assert shared['search_query'] == "search_query_a"
        assert shared['iteration'] == 1

        # Step 2: Search
        search = SearchNode()
        await search.exec_async(shared)
        assert len(shared['history']) == 1
        assert "Body A" in shared['history'][0]

        # Step 3: Relevance (returns retry because we mocked side_effect)
        rel = RelevanceNode()
        action = await rel.exec_async(shared)
        assert action == "retry"

        # Step 4: QueryGen (should see history in prompt - hard to check without spying on generate prompt)
        await qgen.exec_async(shared)
        assert shared['search_query'] == "search_query_b"
        assert shared['iteration'] == 2

        # Step 5: Search
        await search.exec_async(shared)
        assert len(shared['history']) == 2
        assert "Body A" in shared['history'][0]
        assert "Body B" in shared['history'][1]

        # Step 6: Relevance
        action = await rel.exec_async(shared)
        assert action == "success"

from unittest.mock import patch
