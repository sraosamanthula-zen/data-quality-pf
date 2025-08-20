"""
WebSocket API endpoints for real-time updates
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket_manager import websocket_manager
from app.db import JobRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/updates")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time updates.
    Clients can connect to receive live updates about jobs and statistics.
    """
    try:
        await websocket_manager.connect(websocket, client_id)
        
        # Send initial connection confirmation only
        await websocket_manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to data quality platform"
        }, websocket)
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received message from {client_id}: {data}")
                
                # Handle client requests
                if data == "ping":
                    await websocket_manager.send_personal_message({"type": "pong"}, websocket)
                elif data == "get_initial_data":
                    await send_initial_data(websocket)
                elif data == "get_current_data":
                    await send_current_data(websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        websocket_manager.disconnect(websocket)


async def send_initial_data(websocket: WebSocket):
    """Send initial data when client connects"""
    try:
        from app.db import get_db_session
        from app.api.stats import get_statistics
        
        # Get current statistics
        try:
            stats = await get_statistics()
            await websocket_manager.send_personal_message({
                "type": "stats_update",
                "data": stats.dict(),
                "is_initial": True
            }, websocket)
        except Exception as e:
            logger.error(f"Error sending initial stats: {e}")
        
        # Get current jobs list
        try:
            with get_db_session() as db:
                jobs = db.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(50).all()
                jobs_data = []
                for job in jobs:
                    jobs_data.append({
                        "id": job.id,
                        "filename": job.filename,
                        "status": job.status,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "error_message": job.error_message,
                        "quality_score": job.quality_score,
                        "selected_ucs": job.selected_ucs
                    })
                
                await websocket_manager.send_personal_message({
                    "type": "jobs_list_update", 
                    "data": jobs_data,
                    "is_initial": True
                }, websocket)
        except Exception as e:
            logger.error(f"Error sending initial jobs: {e}")
            
    except Exception as e:
        logger.error(f"Error sending initial data: {e}")


async def send_current_data(websocket: WebSocket):
    """Send current data on client request"""
    await send_initial_data(websocket)


@router.get("/connection-info")
async def get_websocket_info():
    """Get information about active WebSocket connections"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "status": "active"
    }
