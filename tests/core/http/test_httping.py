# -*- coding: utf-8 -*-
"""
httping module tests
"""

import pytest

from hio import help
from hio.core import http


logger = help.ogler.getLogger()


def test_http_error():
    """
    Test HTTPError class
    """

    error = http.HTTPError(status=400)
    assert error.status == 400
    assert error.reason == 'Bad Request'
    assert error.title == ""
    assert error.detail == ""
    assert error.fault is None
    assert error.headers == dict()

    body = error.render()
    assert body == b'400 Bad Request\n\n\n'
    body = error.render(jsonify=True)
    assert body == (b'{\n  "status": 400,\n  "reason": "Bad Request",\n'
                            b'  "title": "",\n  "detail":'
                            b' "",\n  "fault": null\n}')


    error = http.HTTPError(status=700,
                              title="Validation Error",
                              detail="Bad mojo",
                              fault=50,
                              headers=dict(Accept='application/json'))

    assert error.status == 700
    assert error.reason == 'Unknown'
    assert error.title == "Validation Error"
    assert error.detail == "Bad mojo"
    assert error.fault == 50
    assert error.headers == dict(Accept='application/json')

    body = error.render()
    assert body == b'700 Unknown\nValidation Error\nBad mojo\n50'
    body = error.render(jsonify=True)
    assert body == (b'{\n  "status": 700,\n  "reason": "Unknown",\n'
                            b'  "title": "Validation Error",'
                            b'\n  "detail": "Bad mojo",\n  "fault": 50\n}')



if __name__ == '__main__':
    test_http_error()
