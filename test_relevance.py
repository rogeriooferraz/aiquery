#!/usr/bin/env python3
import aiquery
from aiquery import SearchBotBase
from ddgs.http_client import HttpClient
import pytest

# Silence ddgs impersonation warnings by forcing internal defaults
HttpClient._impersonates = (None,)
HttpClient._impersonates_os = (None,)

def test_rank_context_weather_priority():
    bot = SearchBotBase()
    search_query = "temperatura São Paulo"
    
    # Mock context list
    context_list = [
        "Result: São Paulo - São Paulo é uma cidade brasileira.",
        "Result: Previsão do tempo - Sol em SP.",
        "Result: Tempo Agora em São Paulo - 04:00 21.9º",
        "Result: Alerta - Chuva intensa em São Paulo."
    ]
    
    ranked = bot.rank_context(search_query, context_list)
    
    # The one with numerical values (21.9 graus) should be cleaned and at the top
    assert "21.9 graus" in sorted_list_to_str(ranked).split('\n')[0]

def sorted_list_to_str(lst):
    return "\n".join(lst)

def test_rank_context_general():
    bot = SearchBotBase()
    search_query = "ganhador oscar 2024"
    
    context_list = [
        "Result: Oscar 2024 - 'Oppenheimer' leva melhor filme.",
        "Result: Previsão tempo - 25 graus.",
        "Result: Cinema - Notícias de Hollywood."
    ]
    
    ranked = bot.rank_context(search_query, context_list)
    
    # Oscar should be at the top
    assert "Oppenheimer" in sorted_list_to_str(ranked).split('\n')[0]

def test_clean_snippet():
    bot = SearchBotBase()
    assert "21.9 graus" in bot.clean_snippet("Tempo: 21.9º")
    assert "25 graus" in bot.clean_snippet("Temp: 25°")
    assert "Mínima: 20" in bot.clean_snippet("Min: 20")

def test_rank_context_no_weather():
    bot = SearchBotBase()
    search_query = "ganhador jogo Palmeiras"
    
    context_list = [
        "Result: Palmeiras vence Grêmio por 2 a 1.",
        "Result: Clima em São Paulo - 25 graus",
        "Result: Notícias do dia - Política e Economia."
    ]
    
    ranked = bot.rank_context(search_query, context_list)
    
    # Should maintain relevance based on Palmeiras keywords
    assert "Palmeiras" in sorted_list_to_str(ranked).split('\n')[0]
