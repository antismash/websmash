#!/usr/bin/env python
from websmash import app, db

db.create_all()
app.run(debug=True)
