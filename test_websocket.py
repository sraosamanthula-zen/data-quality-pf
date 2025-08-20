#!/usr/bin/env python3
"""
Simple WebSocket test client to verify the WebSocket endpoint is working
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/updates"
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Listen for a few messages
            try:
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📨 Received: {message}")
            except asyncio.TimeoutError:
                print("⏰ No messages received within timeout")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
