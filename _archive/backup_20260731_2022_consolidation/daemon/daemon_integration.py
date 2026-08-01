#!/usr/bin/env python3
"""
Nova Voice Integration for Existing Daemon/API Environment
"""
import asyncio
import threading
from queue import Queue
from typing import Optional, Dict, Any
import logging
from nova_voice import NovaOpenAIVoice

logger = logging.getLogger(__name__)

class NovaVoiceDaemon:
    """Thread-safe voice daemon for integration with existing services"""
    
    def __init__(self):
        self.voice = NovaOpenAIVoice()
        self.speech_queue = Queue()
        self.is_running = False
        self.worker_thread = None
        
    def start(self):
        """Start the voice daemon"""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("🔮 Nova Voice Daemon started")
        
    def stop(self):
        """Stop the voice daemon"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("🛑 Nova Voice Daemon stopped")
        
    def speak(self, text: str, priority: int = 1, **kwargs) -> str:
        """
        Add speech to queue (thread-safe)
        
        Args:
            text: Text to speak
            priority: Priority (1=high, 2=normal, 3=low)
            **kwargs: Additional voice parameters (speed, voice, etc.)
            
        Returns:
            str: Job ID for tracking
        """
        import uuid
        job_id = str(uuid.uuid4())[:8]
        
        job = {
            'id': job_id,
            'text': text,
            'priority': priority,
            'kwargs': kwargs
        }
        
        self.speech_queue.put(job)
        logger.info(f"🎵 Queued speech job {job_id}: {text[:50]}...")
        return job_id
        
    def _worker_loop(self):
        """Worker thread that processes speech queue"""
        while self.is_running:
            try:
                # Get job from queue (blocks for 1 second)
                job = self.speech_queue.get(timeout=1)
                
                # Apply any voice settings from kwargs
                if 'voice' in job['kwargs']:
                    self.voice.set_voice(job['kwargs']['voice'])
                if 'volume' in job['kwargs']:
                    self.voice.set_volume(job['kwargs']['volume'])
                
                # Speak the text
                success = self.voice.speak(
                    job['text'], 
                    speed=job['kwargs'].get('speed', 1.0)
                )
                
                if success:
                    logger.info(f"✅ Completed speech job {job['id']}")
                else:
                    logger.error(f"❌ Failed speech job {job['id']}")
                    
                self.speech_queue.task_done()
                
            except Exception as e:
                if self.is_running:  # Only log if we're supposed to be running
                    logger.error(f"❌ Error in voice worker: {e}")


class NovaVoiceAPI:
    """REST API wrapper for voice functionality"""
    
    def __init__(self, daemon: NovaVoiceDaemon):
        self.daemon = daemon
        
    def handle_speak_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle API request for speech synthesis
        
        Expected data format:
        {
            "text": "Text to speak",
            "voice": "nova",  # optional
            "speed": 1.0,     # optional
            "volume": 0.8,    # optional
            "priority": 1     # optional
        }
        """
        try:
            text = data.get('text', '').strip()
            if not text:
                return {
                    'success': False,
                    'error': 'Text is required',
                    'job_id': None
                }
            
            # Extract parameters
            voice_params = {
                'voice': data.get('voice'),
                'speed': data.get('speed', 1.0),
                'volume': data.get('volume'),
            }
            
            # Remove None values
            voice_params = {k: v for k, v in voice_params.items() if v is not None}
            
            # Queue the speech
            job_id = self.daemon.speak(
                text=text,
                priority=data.get('priority', 1),
                **voice_params
            )
            
            return {
                'success': True,
                'job_id': job_id,
                'message': f'Speech queued successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'job_id': None
            }


# =============================================================================
# INTEGRATION EXAMPLES FOR DIFFERENT FRAMEWORKS
# =============================================================================

# ------------------------- FLASK INTEGRATION -------------------------
def flask_integration():
    """Example Flask integration"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    voice_daemon = NovaVoiceDaemon()
    voice_api = NovaVoiceAPI(voice_daemon)
    
    # Start daemon when Flask starts
    voice_daemon.start()
    
    @app.route('/voice/speak', methods=['POST'])
    def speak():
        return jsonify(voice_api.handle_speak_request(request.json))
    
    @app.route('/voice/status', methods=['GET'])
    def status():
        return jsonify({
            'daemon_running': voice_daemon.is_running,
            'queue_size': voice_daemon.speech_queue.qsize()
        })
    
    # Cleanup when Flask shuts down
    @app.teardown_appcontext
    def cleanup(error):
        voice_daemon.stop()
    
    return app

# ------------------------- FASTAPI INTEGRATION -------------------------
async def fastapi_integration():
    """Example FastAPI integration"""
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    class SpeechRequest(BaseModel):
        text: str
        voice: Optional[str] = "nova"
        speed: Optional[float] = 1.0
        volume: Optional[float] = 0.8
        priority: Optional[int] = 1
    
    app = FastAPI()
    voice_daemon = NovaVoiceDaemon()
    voice_api = NovaVoiceAPI(voice_daemon)
    
    @app.on_event("startup")
    async def startup():
        voice_daemon.start()
    
    @app.on_event("shutdown")
    async def shutdown():
        voice_daemon.stop()
    
    @app.post("/voice/speak")
    async def speak(request: SpeechRequest):
        return voice_api.handle_speak_request(request.dict())
    
    @app.get("/voice/status")
    async def status():
        return {
            'daemon_running': voice_daemon.is_running,
            'queue_size': voice_daemon.speech_queue.qsize()
        }
    
    return app

# ------------------------- ASYNCIO SERVICE INTEGRATION -------------------------
class NovaVoiceService:
    """Async service integration"""
    
    def __init__(self):
        self.voice = NovaOpenAIVoice()
        self.speech_queue = asyncio.Queue()
        self.is_running = False
        self.worker_task = None
        
    async def start(self):
        """Start the async voice service"""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._async_worker())
        logger.info("🔮 Nova Voice Service started")
        
    async def stop(self):
        """Stop the async voice service"""
        self.is_running = False
        if self.worker_task:
            await self.worker_task
        logger.info("🛑 Nova Voice Service stopped")
        
    async def speak_async(self, text: str, **kwargs) -> str:
        """Add speech to async queue"""
        import uuid
        job_id = str(uuid.uuid4())[:8]
        
        await self.speech_queue.put({
            'id': job_id,
            'text': text,
            'kwargs': kwargs
        })
        
        return job_id
        
    async def _async_worker(self):
        """Async worker that processes speech queue"""
        while self.is_running:
            try:
                # Wait for job with timeout
                job = await asyncio.wait_for(
                    self.speech_queue.get(), 
                    timeout=1.0
                )
                
                # Process the speech asynchronously
                success = await self.voice.speak_async(
                    job['text'],
                    **job['kwargs']
                )
                
                if success:
                    logger.info(f"✅ Completed async speech job {job['id']}")
                else:
                    logger.error(f"❌ Failed async speech job {job['id']}")
                    
            except asyncio.TimeoutError:
                continue  # No jobs in queue, continue waiting
            except Exception as e:
                logger.error(f"❌ Error in async voice worker: {e}")

# ------------------------- SIMPLE FUNCTION CALLS -------------------------
def simple_integration_example():
    """Simple function-based integration for existing APIs"""
    
    # Global voice instance (thread-safe for reads)
    _voice_instance = None
    
    def get_voice():
        """Get or create voice instance"""
        global _voice_instance
        if _voice_instance is None:
            _voice_instance = NovaOpenAIVoice()
        return _voice_instance
    
    def nova_speak(text: str, voice: str = "nova", speed: float = 1.0) -> bool:
        """Simple function to add to existing API"""
        try:
            voice_instance = get_voice()
            voice_instance.set_voice(voice)
            return voice_instance.speak(text, speed=speed)
        except Exception as e:
            logger.error(f"❌ Nova speak error: {e}")
            return False
    
    async def nova_speak_async(text: str, voice: str = "nova", speed: float = 1.0) -> bool:
        """Simple async function to add to existing API"""
        try:
            voice_instance = get_voice()
            voice_instance.set_voice(voice)
            return await voice_instance.speak_async(text, speed=speed)
        except Exception as e:
            logger.error(f"❌ Nova async speak error: {e}")
            return False
    
    return nova_speak, nova_speak_async

# ------------------------- WEBHOOK INTEGRATION -------------------------
def webhook_handler(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle webhooks that trigger voice synthesis"""
    
    voice_daemon = NovaVoiceDaemon()
    voice_daemon.start()
    
    try:
        # Extract text from webhook payload
        text = webhook_data.get('message', {}).get('text', '')
        
        if not text:
            return {'status': 'error', 'message': 'No text found in webhook'}
        
        # Determine voice settings based on webhook source
        voice_settings = {
            'voice': 'nova',
            'speed': 1.0,
        }
        
        # Customize based on webhook source
        source = webhook_data.get('source', 'unknown')
        if source == 'urgent_alert':
            voice_settings.update({'voice': 'onyx', 'speed': 1.2})
        elif source == 'notification':
            voice_settings.update({'voice': 'shimmer', 'speed': 0.9})
        
        # Queue the speech
        job_id = voice_daemon.speak(text, priority=1, **voice_settings)
        
        return {
            'status': 'success',
            'job_id': job_id,
            'message': f'Voice synthesis queued'
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook handler error: {e}")
        return {'status': 'error', 'message': str(e)}
    finally:
        voice_daemon.stop()


# ------------------------- USAGE EXAMPLES -------------------------
if __name__ == "__main__":
    # Example 1: Simple daemon
    daemon = NovaVoiceDaemon()
    daemon.start()
    
    # Queue some speech
    job1 = daemon.speak("Hello from the daemon!", priority=1)
    job2 = daemon.speak("This is a second message.", priority=2)
    
    # Wait a bit then stop
    import time
    time.sleep(10)
    daemon.stop()
    
    # Example 2: Async service
    async def async_example():
        service = NovaVoiceService()
        await service.start()
        
        job_id = await service.speak_async("Hello from async service!")
        await asyncio.sleep(5)
        
        await service.stop()
    
    # Run async example
    # asyncio.run(async_example())