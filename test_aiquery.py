import pytest
import asyncio
from unittest.mock import MagicMock, patch
from aiquery import BaseAsyncNode, QueryGenNode, main, build_flow

@pytest.mark.asyncio
async def test_base_async_node_propagation():
    node = BaseAsyncNode()
    shared = {"test": 1}
    prep_res = await node.prep_async(shared)
    assert prep_res == shared
    
    exec_res = "test_action"
    post_res = await node.post_async(shared, prep_res, exec_res)
    assert post_res == exec_res

@pytest.mark.asyncio
async def test_query_gen_node_integration(mocker):
    # Simplified Mock
    mock_bot = MagicMock()
    mock_bot.model = "test-model"
    # Use AsyncMock for the generate method
    mock_bot.client.generate = mocker.AsyncMock(return_value={"response": "oscar 2024 winner"})
    
    node = QueryGenNode()
    shared = {
        "bot": mock_bot,
        "user_query": "Who won the oscar?",
        "iteration": 0
    }
    
    action = await node.exec_async(shared)
    assert action == "default"
    assert shared["search_query"] == "oscar 2024 winner"
    assert shared["iteration"] == 1
