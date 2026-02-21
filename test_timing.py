import pytest
import asyncio
from unittest.mock import MagicMock, patch
import datetime
from aiquery import main

@pytest.mark.asyncio
async def test_main_with_timing(mocker):
    # Mock dependencies to isolate CLI timing logic
    mock_args = MagicMock(timestamp=True, gui=False, query=None)
    mocker.patch('aiquery.argparse.ArgumentParser.parse_args', return_value=mock_args)
    mocker.patch('aiquery.input', return_value="capital france")
    mocker.patch('aiquery.SearchBotBase', return_value=MagicMock())
    
    # Mock build_flow to return a mock with an async run_async method
    mock_flow_obj = MagicMock()
    mock_flow_obj.run_async = mocker.AsyncMock()
    mocker.patch('aiquery.build_flow', return_value=mock_flow_obj)

    # Capture stdout
    with patch('builtins.print') as mock_print:
        await main()
        
        # Verify timing info was printed
        printed_texts = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        assert any("Initial Timestamp" in text for text in printed_texts)
        assert any("Final Timestamp" in text for text in printed_texts)
        assert any("Elapsed Time" in text for text in printed_texts)

@pytest.mark.asyncio
async def test_main_without_timing(mocker):
    # Mock dependencies
    mock_args = MagicMock(timestamp=False, gui=False, query=None)
    mocker.patch('aiquery.argparse.ArgumentParser.parse_args', return_value=mock_args)
    mocker.patch('aiquery.input', return_value="capital france")
    mocker.patch('aiquery.SearchBotBase', return_value=MagicMock())
    
    mock_flow_obj = MagicMock()
    mock_flow_obj.run_async = mocker.AsyncMock()
    mocker.patch('aiquery.build_flow', return_value=mock_flow_obj)

    # Capture stdout
    with patch('builtins.print') as mock_print:
        await main()
        
        # Verify timing info was NOT printed
        printed_texts = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        assert not any("Initial Timestamp" in text for text in printed_texts)
        assert not any("Elapsed Time" in text for text in printed_texts)
