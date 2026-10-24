import pytest
from moderation import check_content_policy

def test_check_content_policy_terms():
    settings = {
        "content_filter_enabled": True,
        "filtered_terms": ["badword", "scam"],
        "filtered_domains": []
    }
    assert check_content_policy("This contains badword here", settings) is True
    assert check_content_policy("This is a normal message", settings) is False
    assert check_content_policy("Do not scam people", settings) is True

def test_check_content_policy_domains():
    settings = {
        "content_filter_enabled": True,
        "filtered_terms": [],
        "filtered_domains": ["badsite.com"]
    }
    assert check_content_policy("Visit badsite.com for free stuff", settings) is True
    assert check_content_policy("Visit goodsite.com", settings) is False

def test_check_content_policy_disabled():
    settings = {
        "content_filter_enabled": False,
        "filtered_terms": ["badword"],
        "filtered_domains": []
    }
    assert check_content_policy("This has badword", settings) is False
