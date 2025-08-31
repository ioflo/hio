"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""
import os

import pytest
from hio.help import timing


@pytest.fixture()
def mockHelpingNowIso8601(monkeypatch):
    """
    Replace nowIso8601 universally with fixed value for testing
    """

    def mockNowIso8601():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return "2021-06-27T21:26:21.233257+00:00"

    monkeypatch.setattr(timing, "nowIso8601", mockNowIso8601)
