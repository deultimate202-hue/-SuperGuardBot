import pytest
from moderation import check_spam

def test_check_spam_words():
    settings = {
        "anti_spam": True,
        "blocked_words": ["spam", "scam"],
        "blocked_domains": []
    }
    assert check_spam("This is a spam message", settings) is True
    assert check_spam("This is a normal message", settings) is False
    assert check_spam("Do not scam people", settings) is True

def test_check_spam_domains():
    settings = {
        "anti_spam": True,
        "blocked_words": [],
        "blocked_domains": ["badsite.com"]
    }
    assert check_spam("Visit badsite.com for free stuff", settings) is True
    assert check_spam("Visit goodsite.com", settings) is False

def test_check_spam_disabled():
    settings = {
        "anti_spam": False,
        "blocked_words": ["spam"],
        "blocked_domains": []
    }
    assert check_spam("This is spam", settings) is False
