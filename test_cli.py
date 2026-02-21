import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
from aiquery import main

@pytest.mark.asyncio
async def test_cli_direct_query(mocker):
    # Mock sys.argv to simulate: ./aiquery "capital france"
    mock_args = MagicMock(timestamp=False, gui=False, query='capital france')
    mocker.patch('aiquery.argparse.ArgumentParser.parse_args', return_value=mock_args)
    mocker.patch('aiquery.SearchBotBase', return_value=MagicMock())
    
    mock_flow = MagicMock()
    mock_flow.run_async = mocker.AsyncMock()
    mocker.patch('aiquery.build_flow', return_value=mock_flow)
    
    with patch('builtins.print') as mock_print:
        await main()
        # Verify it ran the flow with the correct query
        args, kwargs = mock_flow.run_async.call_args
        shared = args[0]
        assert shared['user_query'] == 'capital france'

@pytest.mark.asyncio
async def test_cli_gui_flag(mocker):
    # Mock sys.argv to simulate: ./aiquery --gui
    mock_args = MagicMock(timestamp=False, gui=True, query=None)
    mocker.patch('aiquery.argparse.ArgumentParser.parse_args', return_value=mock_args)
    
    # Mock the launch_gui function in app.py
    mock_launch = mocker.patch('app.launch_gui')
    
    await main()
    mock_launch.assert_called_once()
