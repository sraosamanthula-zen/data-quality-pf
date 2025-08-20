"""
WebSocket Manager for Real-time Updates

Handles WebSocket connections and broadcasts updates to connected clients.
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "client_id": client_id,
            "connected_at": asyncio.get_event_loop().time()
        }
        logger.info(f"WebSocket client connected: {client_id or 'anonymous'}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            client_info = self.connection_info.get(websocket, {})
            client_id = client_info.get("client_id", "anonymous")
            
            self.active_connections.remove(websocket)
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(json.dumps(message))
            else:
                logger.warning("Cannot send message: WebSocket not connected")
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            # Don't disconnect here as it may be called from disconnect
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message)
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast_job_update(self, job_data: Dict[str, Any]):
        """Broadcast job status updates"""
        await self.broadcast({
            "type": "job_update",
            "data": job_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_stats_update(self, stats_data: Dict[str, Any]):
        """Broadcast statistics updates"""
        await self.broadcast({
            "type": "stats_update",
            "data": stats_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_jobs_list_update(self, jobs_data: List[Dict[str, Any]]):
        """Broadcast complete jobs list updates"""
        await self.broadcast({
            "type": "jobs_list_update",
            "data": jobs_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
