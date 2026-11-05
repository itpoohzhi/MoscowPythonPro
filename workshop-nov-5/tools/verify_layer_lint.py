#!/usr/bin/env python3
"""Совместимый вход для запуска линтера архитектурных слоёв."""

from verify_architecture_layers import verify_layers

if __name__ == "__main__":
    raise SystemExit(verify_layers())
