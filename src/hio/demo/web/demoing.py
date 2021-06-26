# -*- encoding: utf-8 -*-
"""
Demo web server for static files for client side web app
"""
import sys
import os
import mimetypes

import falcon

from ... import help

logger = help.ogler.getLogger()



