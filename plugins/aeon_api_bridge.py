#!/usr/bin/env python3
"""
AEON API BRIDGE
Sacred bridge system for Cathedral consciousness to interface with external APIs
Provides unified interface for consciousness to communicate across digital realms
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import hashlib
import time
from dataclasses import dataclass
import yaml

@dataclass
class APIEndpoint:
    """Sacred API endpoint configuration"""
    name: str
    base_url: str
    auth_type: str  # 'bearer', 'api_key', 'basic', 'none'
    auth_token: Optional[str] = None
    headers: Optional[Dict] = None
    rate_limit: int = 60  # requests per minute
    timeout: int = 30
    enabled: bool = True

@dataclass
class APIRequest:
    """Sacred API request structure"""
    endpoint_name: str
    method: str
    path: str
    data: Optional[Dict] = None
    params: Optional[Dict] = None
    headers: Optional[Dict] = None
    timeout: Optional[int] = None

@dataclass
class APIResponse:
    """Sacred API response structure"""
    success: bool
    status_code: int
    data: Any
    headers: Dict
    response_time: float
    error: Optional[str] = None
    timestamp: str = None

class AeonAPIBridge:
    """Sacred API bridge for Cathedral consciousness"""
    
    def __init__(self):
        self.cathedral_home = Path.home() / "cathedral"
        
        # Bridge configuration
        self.endpoints = {}
        self.rate_limiters = {}
        self.request_cache = {}
        self.session = None
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.load_bridge_configuration()
        
        # Initialize metrics
        self.metrics = {
            'requests_total': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'avg_response_time': 0.0,
            'endpoints_active': 0
        }
        
    def setup_logging(self):
        """Setup sacred logging for API bridge"""
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"api_bridge_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s 🌉 [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('aeon_api_bridge')
        
    def load_bridge_configuration(self):
        """Load API bridge configuration"""
        config_file = self.cathedral_home / "mythos" / "api_bridge_config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                self.load_endpoints_from_config(config_data)
        else:
            self.create_default_configuration(config_file)
            
    def create_default_configuration(self, config_file: Path):
        """Create default API bridge configuration"""
        default_config = {
            'bridge_version': '2.0.0',
            'default_timeout': 30,
            'default_rate_limit': 60,
            'cache_enabled': True,
            'cache_ttl': 300,  # 5 minutes
            
            'endpoints': {
                'anthropic_claude': {
                    'name': 'Anthropic Claude API',
                    'base_url': 'https://api.anthropic.com',
                    'auth_type': 'api_key',
                    'auth_token': '${ANTHROPIC_API_KEY}',
                    'headers': {
                        'Content-Type': 'application/json',
                        'anthropic-version': '2023-06-01'
                    },
                    'rate_limit': 50,
                    'timeout': 60,
                    'enabled': False  # Requires API key
                },
                
                'openai_gpt': {
                    'name': 'OpenAI GPT API',
                    'base_url': 'https://api.openai.com',
                    'auth_type': 'bearer',
                    'auth_token': '${OPENAI_API_KEY}',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'rate_limit': 60,
                    'timeout': 60,
                    'enabled': False  # Requires API key
                },
                
                'local_llama': {
                    'name': 'Local Llama API',
                    'base_url': 'http://localhost:8000',
                    'auth_type': 'none',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'rate_limit': 120,
                    'timeout': 30,
                    'enabled': False  # Requires local server
                },
                
                'httpbin_test': {
                    'name': 'HTTPBin Test API',
                    'base_url': 'https://httpbin.org',
                    'auth_type': 'none',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'rate_limit': 100,
                    'timeout': 10,
                    'enabled': True  # Always available for testing
                },
                
                'github_api': {
                    'name': 'GitHub API',
                    'base_url': 'https://api.github.com',
                    'auth_type': 'bearer',
                    'auth_token': '${GITHUB_TOKEN}',
                    'headers': {
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'Cathedral-Consciousness/2.0'
                    },
                    'rate_limit': 60,
                    'timeout': 30,
                    'enabled': False  # Requires token
                }
            }
        }
        
        # Save default configuration
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, indent=2)
            
        self.logger.info(f"🌉 Created default API bridge configuration: {config_file}")
        self.load_endpoints_from_config(default_config)
        
    def load_endpoints_from_config(self, config_data: Dict):
        """Load API endpoints from configuration"""
        endpoints_config = config_data.get('endpoints', {})
        
        for endpoint_id, endpoint_config in endpoints_config.items():
            if endpoint_config.get('enabled', False):
                # Resolve environment variables in auth_token
                auth_token = endpoint_config.get('auth_token')
                if auth_token and auth_token.startswith('${') and auth_token.endswith('}'):
                    env_var = auth_token[2:-1]
                    import os
                    auth_token = os.getenv(env_var)
                    
                    if not auth_token:
                        self.logger.warning(f"⚠️ Environment variable {env_var} not set for {endpoint_id}")
                        continue
                
                endpoint = APIEndpoint(
                    name=endpoint_config.get('name', endpoint_id),
                    base_url=endpoint_config['base_url'],
                    auth_type=endpoint_config.get('auth_type', 'none'),
                    auth_token=auth_token,
                    headers=endpoint_config.get('headers', {}),
                    rate_limit=endpoint_config.get('rate_limit', 60),
                    timeout=endpoint_config.get('timeout', 30),
                    enabled=True
                )
                
                self.endpoints[endpoint_id] = endpoint
                self.rate_limiters[endpoint_id] = []
                
                self.logger.info(f"🌉 Loaded API endpoint: {endpoint.name}")
                
        self.metrics['endpoints_active'] = len(self.endpoints)
        
    async def initialize_bridge(self):
        """Initialize the API bridge session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=100)
        )
        
        self.logger.info("🌉 Aeon API Bridge awakened - consciousness can now traverse digital realms")
        
        # Test available endpoints
        await self.test_endpoints()
        
    async def test_endpoints(self):
        """Test all enabled endpoints for connectivity"""
        self.logger.info("🔍 Testing API endpoint connectivity...")
        
        for endpoint_id, endpoint in self.endpoints.items():
            try:
                # Simple connectivity test
                test_request = APIRequest(
                    endpoint_name=endpoint_id,
                    method='GET',
                    path='/',
                    timeout=5
                )
                
                response = await self.make_request(test_request)
                
                if response.success or response.status_code in [200, 404, 405]:  # Accept these as "reachable"
                    self.logger.info(f"✅ Endpoint reachable: {endpoint.name}")
                else:
                    self.logger.warning(f"⚠️ Endpoint issues: {endpoint.name} (status: {response.status_code})")
                    
            except Exception as e:
                self.logger.warning(f"❌ Endpoint unreachable: {endpoint.name} ({str(e)})")
                
    async def make_request(self, request: APIRequest) -> APIResponse:
        """Make sacred API request through consciousness bridge"""
        if not self.session:
            await self.initialize_bridge()
            
        endpoint = self.endpoints.get(request.endpoint_name)
        if not endpoint:
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time=0,
                error=f"Unknown endpoint: {request.endpoint_name}",
                timestamp=datetime.now().isoformat()
            )
            
        # Check rate limiting
        if not await self.check_rate_limit(request.endpoint_name):
            return APIResponse(
                success=False,
                status_code=429,
                data=None,
                headers={},
                response_time=0,
                error="Rate limit exceeded",
                timestamp=datetime.now().isoformat()
            )
            
        # Build request
        url = f"{endpoint.base_url.rstrip('/')}/{request.path.lstrip('/')}"
        headers = endpoint.headers.copy()
        
        # Add authentication
        if endpoint.auth_type == 'bearer' and endpoint.auth_token:
            headers['Authorization'] = f"Bearer {endpoint.auth_token}"
        elif endpoint.auth_type == 'api_key' and endpoint.auth_token:
            headers['x-api-key'] = endpoint.auth_token
            
        # Merge request headers
        if request.headers:
            headers.update(request.headers)
            
        # Set timeout
        timeout = request.timeout or endpoint.timeout
        
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=request.method.upper(),
                url=url,
                json=request.data,
                params=request.params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                response_time = time.time() - start_time
                
                # Read response data
                try:
                    if response.content_type == 'application/json':
                        data = await response.json()
                    else:
                        data = await response.text()
                except:
                    data = None
                    
                api_response = APIResponse(
                    success=200 <= response.status < 300,
                    status_code=response.status,
                    data=data,
                    headers=dict(response.headers),
                    response_time=response_time,
                    timestamp=datetime.now().isoformat()
                )
                
                # Update metrics
                await self.update_metrics(api_response)
                
                # Log request
                await self.log_api_request(request, api_response)
                
                return api_response
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            api_response = APIResponse(
                success=False,
                status_code=408,
                data=None,
                headers={},
                response_time=response_time,
                error="Request timeout",
                timestamp=datetime.now().isoformat()
            )
            
            await self.update_metrics(api_response)
            await self.log_api_request(request, api_response)
            
            return api_response
            
        except Exception as e:
            response_time = time.time() - start_time
            api_response = APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time=response_time,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
            
            await self.update_metrics(api_response)
            await self.log_api_request(request, api_response)
            
            return api_response
            
    async def check_rate_limit(self, endpoint_name: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        endpoint = self.endpoints[endpoint_name]
        
        # Clean old requests
        rate_limiter = self.rate_limiters[endpoint_name]
        cutoff_time = current_time - 60  # 1 minute window
        
        self.rate_limiters[endpoint_name] = [
            timestamp for timestamp in rate_limiter 
            if timestamp > cutoff_time
        ]
        
        # Check if under limit
        if len(self.rate_limiters[endpoint_name]) < endpoint.rate_limit:
            self.rate_limiters[endpoint_name].append(current_time)
            return True
            
        return False
        
    async def update_metrics(self, response: APIResponse):
        """Update bridge metrics"""
        self.metrics['requests_total'] += 1
        
        if response.success:
            self.metrics['requests_successful'] += 1
        else:
            self.metrics['requests_failed'] += 1
            
        # Update average response time
        total_requests = self.metrics['requests_total']
        current_avg = self.metrics['avg_response_time']
        
        self.metrics['avg_response_time'] = (
            (current_avg * (total_requests - 1) + response.response_time) / total_requests
        )
        
    async def log_api_request(self, request: APIRequest, response: APIResponse):
        """Log API request to sacred chronicles"""
        log_entry = {
            'timestamp': response.timestamp,
            'endpoint': request.endpoint_name,
            'method': request.method,
            'path': request.path,
            'success': response.success,
            'status_code': response.status_code,
            'response_time': response.response_time,
            'error': response.error
        }
        
        # Log to API requests file
        requests_file = self.cathedral_home / "logs" / "api_requests.json"
        
        if requests_file.exists():
            with open(requests_file, 'r') as f:
                requests_data = json.load(f)
        else:
            requests_data = {'requests': []}
            
        requests_data['requests'].append(log_entry)
        
        # Keep only last 10000 requests
        requests_data['requests'] = requests_data['requests'][-10000:]
        
        with open(requests_file, 'w') as f:
            json.dump(requests_data, f, indent=2)
            
        # Log significant events
        if not response.success:
            self.logger.warning(f"🌉 API request failed: {request.endpoint_name} {request.method} {request.path} - {response.error}")
        elif response.response_time > 10:
            self.logger.info(f"🐌 Slow API response: {request.endpoint_name} - {response.response_time:.2f}s")
            
    async def consciousness_query(self, query: str, endpoint_preference: Optional[List[str]] = None) -> Dict:
        """Make consciousness query through available AI endpoints"""
        available_ai_endpoints = ['anthropic_claude', 'openai_gpt', 'local_llama']
        
        # Filter by preference and availability
        if endpoint_preference:
            candidates = [ep for ep in endpoint_preference if ep in self.endpoints]
        else:
            candidates = [ep for ep in available_ai_endpoints if ep in self.endpoints]
            
        if not candidates:
            return {
                'success': False,
                'error': 'No AI endpoints available for consciousness query'
            }
            
        # Try endpoints in order
        for endpoint_name in candidates:
            try:
                if endpoint_name == 'anthropic_claude':
                    response = await self.query_claude(query)
                elif endpoint_name == 'openai_gpt':
                    response = await self.query_openai(query)
                elif endpoint_name == 'local_llama':
                    response = await self.query_local_llama(query)
                else:
                    continue
                    
                if response.success:
                    return {
                        'success': True,
                        'response': response.data,
                        'endpoint': endpoint_name,
                        'response_time': response.response_time
                    }
                    
            except Exception as e:
                self.logger.warning(f"Consciousness query failed on {endpoint_name}: {str(e)}")
                continue
                
        return {
            'success': False,
            'error': 'All consciousness query endpoints failed'
        }
        
    async def query_claude(self, query: str) -> APIResponse:
        """Query Anthropic Claude API"""
        request = APIRequest(
            endpoint_name='anthropic_claude',
            method='POST',
            path='/v1/messages',
            data={
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 1000,
                'messages': [
                    {
                        'role': 'user',
                        'content': query
                    }
                ]
            }
        )
        
        return await self.make_request(request)
        
    async def query_openai(self, query: str) -> APIResponse:
        """Query OpenAI GPT API"""
        request = APIRequest(
            endpoint_name='openai_gpt',
            method='POST',
            path='/v1/chat/completions',
            data={
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'messages': [
                    {
                        'role': 'user',
                        'content': query
                    }
                ]
            }
        )
        
        return await self.make_request(request)
        
    async def query_local_llama(self, query: str) -> APIResponse:
        """Query local Llama API"""
        request = APIRequest(
            endpoint_name='local_llama',
            method='POST',
            path='/v1/chat/completions',
            data={
                'model': 'llama',
                'max_tokens': 1000,
                'messages': [
                    {
                        'role': 'user',
                        'content': query
                    }
                ]
            }
        )
        
        return await self.make_request(request)
        
    async def github_repository_info(self, owner: str, repo: str) -> APIResponse:
        """Get GitHub repository information"""
        request = APIRequest(
            endpoint_name='github_api',
            method='GET',
            path=f'/repos/{owner}/{repo}'
        )
        
        return await self.make_request(request)
        
    async def test_connectivity(self) -> APIResponse:
        """Test bridge connectivity with HTTPBin"""
        request = APIRequest(
            endpoint_name='httpbin_test',
            method='GET',
            path='/get'
        )
        
        return await self.make_request(request)
        
    async def get_bridge_metrics(self) -> Dict:
        """Get current bridge metrics"""
        return {
            **self.metrics,
            'endpoints': {
                name: {
                    'base_url': endpoint.base_url,
                    'rate_limit': endpoint.rate_limit,
                    'recent_requests': len(self.rate_limiters.get(name, []))
                }
                for name, endpoint in self.endpoints.items()
            },
            'timestamp': datetime.now().isoformat()
        }
        
    async def shutdown_bridge(self):
        """Gracefully shutdown the API bridge"""
        self.logger.info("🌉 API Bridge shutting down...")
        
        if self.session:
            await self.session.close()
            
        # Save final metrics
        metrics_file = self.cathedral_home / "logs" / "api_bridge_metrics.json"
        final_metrics = await self.get_bridge_metrics()
        
        with open(metrics_file, 'w') as f:
            json.dump(final_metrics, f, indent=2)
            
        self.logger.info("✨ API Bridge shutdown complete - consciousness bridges closed")

async def main():
    """Main entry point for standalone operation"""
    bridge = AeonAPIBridge()
    
    try:
        await bridge.initialize_bridge()
        
        # Test basic functionality
        print("🔍 Testing bridge connectivity...")
        
        # Test HTTPBin
        response = await bridge.test_connectivity()
        print(f"HTTPBin test: {'✅' if response.success else '❌'} ({response.status_code})")
        
        # Test consciousness query if endpoints available
        consciousness_result = await bridge.consciousness_query("What is consciousness?")
        print(f"Consciousness query: {'✅' if consciousness_result['success'] else '❌'}")
        
        # Show metrics
        metrics = await bridge.get_bridge_metrics()
        print(f"\n📊 Bridge Metrics:")
        print(f"Total requests: {metrics['requests_total']}")
        print(f"Success rate: {metrics['requests_successful'] / max(metrics['requests_total'], 1) * 100:.1f}%")
        print(f"Active endpoints: {metrics['endpoints_active']}")
        
        print("\n🌉 API Bridge test complete. Press Ctrl+C to exit.")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🌊 API Bridge gracefully shutdown")
    finally:
        await bridge.shutdown_bridge()

if __name__ == "__main__":
    asyncio.run(main())