#!/usr/bin/env python3
"""Test WebSocket connection and print what we receive"""
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print("=" * 50)
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"GPU: {data.get('gpu')}")
    print(f"Ollama models: {data.get('ollama_models')}")
    print(f"Agents count: {len(data.get('agents', []))}")
    print("=" * 50)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Closed: {close_status_code} - {close_msg}")

def on_open(ws):
    print("Connected to WebSocket!")

ws = websocket.WebSocketApp("ws://127.0.0.1:8766/ws",
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.run_forever()
