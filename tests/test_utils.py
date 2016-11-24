#!/usr/bin/env python
"""Tests for utility functions"""
from minimock import TraceTracker, assert_same_trace
from websmash.utils import generate_confirmation_mail


def test_generate_confirmation_mail():
    """Test generation of a confirmation email"""
    # abuse the TraceTracker to make use of doctest features
    tt = TraceTracker()
    mail = generate_confirmation_mail(message="Test!")

    tt.out.write(mail)

    expected = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:
<BLANKLINE>
Test!
"""

    assert_same_trace(tt, expected)
