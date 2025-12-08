# app/handlers/__init__.py

# Import start handler
from app.handlers.start import start_handler

# Import sources handlers
from app.handlers.sources import sources_handlers

# Import destinations handlers  
from app.handlers.destinations import destinations_handlers

# Import posts handlers
from app.handlers.posts import posts_handlers

# Import intervals handlers
from app.handlers.intervals import intervals_handlers

# Import forwarding handlers
from app.handlers.forwarding import forwarding_handlers, channel_post_handler

__all__ = [
    'start_handler',
    'sources_handlers',
    'destinations_handlers',
    'posts_handlers',
    'intervals_handlers',
    'forwarding_handlers',
    'channel_post_handler'
]
