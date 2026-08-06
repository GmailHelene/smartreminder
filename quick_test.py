#!/usr/bin/env python3
import os
os.environ['TESTING'] = '1'

try:
    from app import app
    with app.app_context():
        filters = ['nl2br', 'as_datetime', 'strftime']
        for f in filters:
            exists = f in app.jinja_env.filters
            print(f"{f}: {exists}")
        
        # Test strftime specifically
        as_dt = app.jinja_env.filters['as_datetime']
        strf = app.jinja_env.filters['strftime']
        
        date_obj = as_dt("2024-12-01 10:30")
        result = strf(date_obj, '%d.%m.%Y %H:%M')
        print(f"Filter test: {result}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
