"""Routers FastAPI."""

from . import auth, users, posts, follows, likes, feed

__all__ = ["auth", "users", "posts", "follows", "likes", "feed"]
