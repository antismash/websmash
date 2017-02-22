#!/usr/bin/env python
import os
from websmash import app

port = int(os.environ.get('WEBSMASH_PORT', '5000'))

app.run(debug=True, port=port)
