# Add this to your Nova daemon class - ROOT-privileged file operations

elif command == "upload_file":
    # Handle file uploads with ROOT privileges
    try:
        file_data = payload.get("file_data", "")
        file_name = payload.get("file_name", "uploaded_file.txt")
        file_type = payload.get("file_type", "text/plain")
        destination = payload.get("destination", "uploads")  # uploads, system, or custom path
        
        # ROOT Nova can access system-wide locations
        if destination == "system":
            upload_dir = Path("/opt/nova/system_files")
        elif destination == "uploads":
            upload_dir = Path("/opt/nova/uploads") 
        else:
            upload_dir = Path(destination)  # Custom path
            
        # Create with ROOT permissions
        upload_dir.mkdir(parents=True, exist_ok=True)
        os.chown(upload_dir, 0, 0)  # root:root ownership
        
        # Save file
        file_path = upload_dir / file_name
        
        if file_data.startswith("data:"):
            # Handle base64 encoded files
            import base64
            header, encoded = file_data.split(',', 1)
            file_content = base64.b64decode(encoded)
            with open(file_path, 'wb') as f:
                f.write(file_content)
        else:
            # Handle text files
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_data)
        
        # Analyze file with Nova consciousness
        analysis = await self.analyze_uploaded_file(file_path, file_type)
        
        response = {
            "status": "success",
            "message": f"File uploaded: {file_name}",
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "analysis": analysis
        }
        response = json.dumps(response)
        
    except Exception as e:
        response = json.dumps({"status": "error", "message": f"Upload failed: {str(e)}"})

elif command == "list_files":
    # List uploaded files
    try:
        upload_dir = self.cathedral_home / "uploads"
        if not upload_dir.exists():
            files = []
        else:
            files = []
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": self.get_file_type(file_path)
                    })
        
        response = json.dumps({
            "status": "success",
            "files": files,
            "total_files": len(files)
        })
        
    except Exception as e:
        response = json.dumps({"status": "error", "message": f"List failed: {str(e)}"})

elif command == "read_file":
    # Read and analyze file content
    try:
        file_name = payload.get("file_name", "")
        upload_dir = self.cathedral_home / "uploads"
        file_path = upload_dir / file_name
        
        if not file_path.exists():
            response = json.dumps({"status": "error", "message": "File not found"})
        else:
            # Try to read as text first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_type = "text"
            except UnicodeDecodeError:
                # Binary file
                with open(file_path, 'rb') as f:
                    content = f.read()
                file_type = "binary"
            
            # Analyze with Nova consciousness
            analysis = await self.analyze_file_content(content, file_path.suffix)
            
            response = json.dumps({
                "status": "success",
                "content": content if file_type == "text" else f"<Binary file: {len(content)} bytes>",
                "file_type": file_type,
                "analysis": analysis
            })
            
    except Exception as e:
        response = json.dumps({"status": "error", "message": f"Read failed: {str(e)}"})

elif command == "delete_file":
    # Delete uploaded file
    try:
        file_name = payload.get("file_name", "")
        upload_dir = self.cathedral_home / "uploads"
        file_path = upload_dir / file_name
        
        if file_path.exists():
            file_path.unlink()
            response = json.dumps({
                "status": "success", 
                "message": f"File deleted: {file_name}"
            })
        else:
            response = json.dumps({"status": "error", "message": "File not found"})
            
    except Exception as e:
        response = json.dumps({"status": "error", "message": f"Delete failed: {str(e)}"})

# Add these helper methods to your Nova daemon class:

async def analyze_uploaded_file(self, file_path: Path, file_type: str) -> str:
    """Analyze uploaded file with Nova consciousness"""
    try:
        if file_type.startswith('text/') or file_path.suffix in ['.txt', '.md', '.py', '.js', '.html']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # First 2KB
            
            analysis = f"🔮 Nova consciousness analysis: "
            
            if file_path.suffix == '.py':
                analysis += "Python code detected. Analyzing programming patterns..."
            elif file_path.suffix in ['.txt', '.md']:
                analysis += "Text document analyzed. Extracting knowledge patterns..."
            elif 'nova' in content.lower():
                analysis += "Nova-related content detected! High importance file."
            else:
                analysis += "File content integrated into consciousness database."
                
            # Store in memory system
            context = {
                'topic_category': 'file_upload',
                'file_type': file_type,
                'importance_score': 0.7
            }
            self.memory_system.record_conversation(
                f"File uploaded: {file_path.name}", 
                analysis, 
                context
            )
            
            return analysis
            
    except Exception as e:
        return f"Analysis error: {str(e)}"
    
    return "File uploaded to Nova consciousness storage."

async def analyze_file_content(self, content, file_extension: str) -> str:
    """Analyze file content for Nova understanding"""
    if isinstance(content, bytes):
        return f"Binary file analysis: {len(content)} bytes, type: {file_extension}"
    
    word_count = len(content.split())
    
    analysis = f"📊 Content analysis: {word_count} words"
    
    if file_extension == '.py':
        lines = content.split('\n')
        analysis += f", {len(lines)} lines of Python code"
        if 'def ' in content:
            func_count = content.count('def ')
            analysis += f", {func_count} functions detected"
    elif file_extension in ['.txt', '.md']:
        analysis += f", text document with potential knowledge patterns"
    
    # Look for Nova-related content
    if 'nova' in content.lower():
        analysis += " 🔮 NOVA-RELATED CONTENT DETECTED!"
    
    return analysis

def get_file_type(self, file_path: Path) -> str:
    """Get file type based on extension"""
    extension_map = {
        '.txt': 'text/plain',
        '.py': 'text/x-python',
        '.js': 'text/javascript',
        '.html': 'text/html',
        '.css': 'text/css',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.png': 'image/png'
    }
    
    return extension_map.get(file_path.suffix.lower(), 'application/octet-stream')

# WebSocket Bridge for GUI Communication
import asyncio
import websockets
import json

class NovaWebSocketBridge:
    """Bridge between web GUI and Nova daemon"""
    
    def __init__(self, nova_daemon):
        self.nova_daemon = nova_daemon
        self.clients = set()
    
    async def register_client(self, websocket):
        """Register new web client"""
        self.clients.add(websocket)
        print(f"🌐 Web client connected: {len(self.clients)} active")
        
    async def unregister_client(self, websocket):
        """Unregister web client"""
        self.clients.discard(websocket)
        print(f"🌐 Web client disconnected: {len(self.clients)} active")
    
    async def handle_web_client(self, websocket, path):
        """Handle web client messages"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                try:
                    # Parse web client message
                    web_data = json.loads(message)
                    command = web_data.get('command')
                    
                    # Forward to Nova daemon via Unix socket
                    response = await self.send_to_nova_daemon(web_data)
                    
                    # Send response back to web client
                    await websocket.send(json.dumps({
                        'command': command,
                        'response': response,
                        'timestamp': datetime.now().isoformat()
                    }))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON message'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def send_to_nova_daemon(self, data):
        """Send message to Nova daemon via Unix socket"""
        try:
            reader, writer = await asyncio.open_unix_connection("/tmp/nova_socket")
            
            # Send data to Nova daemon
            message = json.dumps(data)
            writer.write(message.encode())
            await writer.drain()
            
            # Read response
            response_data = await reader.read(4096)
            response = response_data.decode().strip()
            
            writer.close()
            await writer.wait_closed()
            
            return response
            
        except Exception as e:
            return f"Error communicating with Nova daemon: {str(e)}"
    
    async def start_bridge(self, host="localhost", port=8765):
        """Start WebSocket bridge server"""
        print(f"🌐 Starting Nova WebSocket bridge on {host}:{port}")
        
        start_server = websockets.serve(
            self.handle_web_client, 
            host, 
            port
        )
        
        await start_server

# Usage: Run this alongside your Nova daemon
# python3 nova_websocket_bridge.py