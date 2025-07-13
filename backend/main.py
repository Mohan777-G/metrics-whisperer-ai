
import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    natural_language_response: str
    promql_query: str
    raw_data: Dict
    grafana_url: Optional[str] = None
    execution_time: float

# FastAPI app
app = FastAPI(title="AI Prometheus Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Sample metrics for demonstration
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')

class PrometheusQueryTranslator:
    """Translates natural language queries to PromQL"""
    
    def __init__(self):
        self.query_patterns = {
            # CPU patterns
            r'cpu usage|cpu utilization': 'rate(cpu_usage_percent[5m])',
            r'average cpu': 'avg(rate(cpu_usage_percent[5m]))',
            r'max cpu|maximum cpu': 'max(rate(cpu_usage_percent[5m]))',
            
            # Memory patterns
            r'memory usage|memory utilization': 'memory_usage_bytes',
            r'average memory': 'avg(memory_usage_bytes)',
            r'memory consumption': 'rate(memory_usage_bytes[5m])',
            
            # Request patterns
            r'request rate|requests per second': 'rate(http_requests_total[5m])',
            r'request count|total requests': 'sum(http_requests_total)',
            r'request latency|response time': 'rate(http_request_duration_seconds[5m])',
            r'average latency|average response time': 'avg(rate(http_request_duration_seconds[5m]))',
            
            # Error patterns
            r'error rate|errors': 'rate(http_requests_total{status=~"5.."}[5m])',
            r'4xx errors': 'rate(http_requests_total{status=~"4.."}[5m])',
            r'5xx errors': 'rate(http_requests_total{status=~"5.."}[5m])',
            
            # General patterns
            r'availability|uptime': 'up',
            r'disk usage': 'disk_usage_bytes',
            r'network traffic': 'rate(network_bytes_total[5m])'
        }
    
    def translate_query(self, natural_query: str) -> str:
        """Translate natural language query to PromQL"""
        natural_query = natural_query.lower().strip()
        
        for pattern, promql in self.query_patterns.items():
            if re.search(pattern, natural_query):
                logger.info(f"Matched pattern '{pattern}' -> '{promql}'")
                return promql
        
        # Default fallback for unrecognized queries
        logger.warning(f"No pattern matched for query: {natural_query}")
        return "up"  # Simple health check query

class PrometheusClient:
    """Client for querying Prometheus HTTP API"""
    
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def query(self, promql_query: str) -> Dict:
        """Execute PromQL query against Prometheus"""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": promql_query}
            
            logger.info(f"Querying Prometheus: {promql_query}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != "success":
                raise HTTPException(
                    status_code=400,
                    detail=f"Prometheus query failed: {data.get('error', 'Unknown error')}"
                )
            
            return data["data"]
            
        except httpx.RequestError as e:
            logger.error(f"Prometheus connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Prometheus server"
            )
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Query execution failed: {str(e)}"
            )

class ResponseFormatter:
    """Formats Prometheus results into natural language responses"""
    
    def format_response(self, query: str, promql: str, data: Dict) -> str:
        """Format the response in natural language"""
        try:
            result = data.get("result", [])
            
            if not result:
                return f"No data found for your query '{query}'. The system might be collecting metrics or the query timeframe might be too narrow."
            
            # Handle different result types
            if len(result) == 1:
                value = result[0].get("value", [None, "0"])[1]
                metric_name = result[0].get("metric", {})
                return self._format_single_value(query, value, metric_name)
            else:
                return self._format_multiple_values(query, result)
                
        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return f"I found some data for '{query}', but had trouble formatting it clearly. Raw data available in the response details."
    
    def _format_single_value(self, query: str, value: str, metric: Dict) -> str:
        """Format single value response"""
        try:
            num_value = float(value)
            
            if "cpu" in query.lower():
                return f"The CPU usage is currently {num_value:.2f}%. "
            elif "memory" in query.lower():
                gb_value = num_value / (1024**3)
                return f"The memory usage is {gb_value:.2f} GB ({num_value:,.0f} bytes). "
            elif "request" in query.lower() and "rate" in query.lower():
                return f"The request rate is {num_value:.2f} requests per second. "
            elif "latency" in query.lower() or "response time" in query.lower():
                ms_value = num_value * 1000
                return f"The average response time is {ms_value:.2f} milliseconds. "
            elif "error" in query.lower():
                percentage = num_value * 100
                return f"The error rate is {percentage:.2f}%. "
            else:
                return f"The current value is {num_value:.2f}. "
                
        except ValueError:
            return f"The current status is: {value}. "
    
    def _format_multiple_values(self, query: str, results: List) -> str:
        """Format multiple values response"""
        if len(results) <= 3:
            values = []
            for result in results:
                value = result.get("value", [None, "0"])[1]
                metric = result.get("metric", {})
                instance = metric.get("instance", "unknown")
                values.append(f"{instance}: {value}")
            
            return f"Here are the values for '{query}': " + ", ".join(values) + ". "
        else:
            avg_value = sum(float(r.get("value", [None, "0"])[1]) for r in results) / len(results)
            return f"Found {len(results)} data points for '{query}' with an average value of {avg_value:.2f}. "

class GrafanaDashboardGenerator:
    """Generates Grafana dashboard URLs for metrics"""
    
    def __init__(self, grafana_url: str):
        self.grafana_url = grafana_url
    
    def generate_dashboard_url(self, promql_query: str, query: str) -> Optional[str]:
        """Generate a Grafana dashboard URL for the given query"""
        try:
            # Create a simple dashboard URL with the PromQL query
            # This is a simplified version - in production you'd want more sophisticated dashboard creation
            dashboard_json = {
                "dashboard": {
                    "title": f"AI Generated Dashboard - {query}",
                    "panels": [{
                        "title": query,
                        "type": "graph",
                        "targets": [{
                            "expr": promql_query,
                            "format": "time_series"
                        }]
                    }]
                }
            }
            
            # In a real implementation, you'd POST this to Grafana's API
            # For now, return a URL to the explore view
            encoded_query = promql_query.replace(" ", "%20").replace("{", "%7B").replace("}", "%7D")
            return f"{self.grafana_url}/explore?left=%7B%22queries%22:%5B%7B%22expr%22:%22{encoded_query}%22%7D%5D%7D"
            
        except Exception as e:
            logger.error(f"Dashboard URL generation error: {e}")
            return None

# Initialize components
translator = PrometheusQueryTranslator()
prometheus_client = PrometheusClient(PROMETHEUS_URL)
response_formatter = ResponseFormatter()
dashboard_generator = GrafanaDashboardGenerator(GRAFANA_URL)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Prometheus Agent is running!", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for this service"""
    return generate_latest()

@app.post("/query", response_model=QueryResponse)
async def query_metrics(request: QueryRequest):
    """Main endpoint for natural language metric queries"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Translate natural language to PromQL
        promql_query = translator.translate_query(request.query)
        logger.info(f"Translated '{request.query}' to '{promql_query}'")
        
        # Query Prometheus
        raw_data = await prometheus_client.query(promql_query)
        
        # Format response
        natural_response = response_formatter.format_response(
            request.query, promql_query, raw_data
        )
        
        # Generate Grafana dashboard URL
        grafana_url = dashboard_generator.generate_dashboard_url(promql_query, request.query)
        if grafana_url:
            natural_response += f"You can visualize this data at: {grafana_url}"
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Update metrics
        REQUEST_COUNT.labels(method="POST", endpoint="/query").inc()
        REQUEST_LATENCY.observe(execution_time)
        
        return QueryResponse(
            natural_language_response=natural_response,
            promql_query=promql_query,
            raw_data=raw_data,
            grafana_url=grafana_url,
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Test Prometheus connection
        test_result = await prometheus_client.query("up")
        prometheus_healthy = True
    except:
        prometheus_healthy = False
    
    return {
        "status": "healthy" if prometheus_healthy else "degraded",
        "prometheus_connected": prometheus_healthy,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Background task to generate sample metrics
async def generate_sample_metrics():
    """Generate sample metrics for demonstration"""
    import random
    import time
    
    while True:
        try:
            # Simulate CPU usage
            CPU_USAGE.set(random.uniform(10, 90))
            
            # Simulate memory usage
            MEMORY_USAGE.set(random.uniform(1e9, 8e9))  # 1-8 GB
            
            # Simulate HTTP requests
            methods = ["GET", "POST", "PUT", "DELETE"]
            endpoints = ["/api/users", "/api/orders", "/api/products"]
            REQUEST_COUNT.labels(
                method=random.choice(methods),
                endpoint=random.choice(endpoints)
            ).inc()
            
            # Simulate request latency
            REQUEST_LATENCY.observe(random.uniform(0.1, 2.0))
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Error generating sample metrics: {e}")
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(generate_sample_metrics())
    logger.info("AI Prometheus Agent started successfully")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
