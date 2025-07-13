
# AI Prometheus Agent

A conversational AI system that translates natural language queries into PromQL and provides intelligent analytics for your Prometheus metrics.

## 🚀 Features

- **Natural Language Processing**: Ask questions in plain English about your metrics
- **Intelligent PromQL Translation**: Automatically converts questions to proper PromQL queries
- **Real-time Metrics**: Query live Prometheus data with instant responses
- **Grafana Integration**: Automatic dashboard URL generation for visualization
- **Modern Web Interface**: Beautiful, responsive React frontend
- **Docker Ready**: Complete containerized deployment with docker-compose
- **Comprehensive Monitoring**: Built-in health checks and performance metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI API   │    │   Prometheus    │
│                 │◄──►│                 │◄──►│                 │
│   Port: 3001    │    │   Port: 8000    │    │   Port: 9090    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Grafana     │
                       │                 │
                       │   Port: 3000    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone and Start

```bash
git clone <your-repo-url>
cd ai-prometheus-agent
docker-compose up -d
```

### 2. Access the Services

- **AI Agent Frontend**: http://localhost:3001
- **FastAPI API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### 3. Try Example Queries

Open the frontend and try these questions:

- "What's the average CPU usage?"
- "Show me the request rate"
- "What's the current memory usage?"
- "What's the error rate?"
- "Show me request latency"

## 🔧 Configuration

### Environment Variables

Create a `.env` file for customization:

```env
# Optional: HuggingFace API key for advanced LLM features
HUGGINGFACE_API_KEY=your_key_here

# Service URLs (defaults shown)
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### Custom Prometheus Configuration

Edit `prometheus/prometheus.yml` to add your own scrape targets:

```yaml
scrape_configs:
  - job_name: "your-app"
    static_configs:
      - targets: ["your-app:port"]
```

## 📊 Supported Query Types

The AI agent understands various types of questions:

### CPU Metrics
- "What's the CPU usage?"
- "Show me average CPU utilization"
- "What's the maximum CPU?"

### Memory Metrics
- "How much memory is being used?"
- "What's the memory consumption?"
- "Show me average memory usage"

### Request Metrics
- "What's the request rate?"
- "How many requests per second?"
- "Show me total requests"

### Performance Metrics
- "What's the response time?"
- "Show me request latency"
- "What's the average latency?"

### Error Metrics
- "What's the error rate?"
- "Show me 4xx errors"
- "How many 5xx errors?"

### System Health
- "Is the system up?"
- "What's the availability?"
- "Show me uptime"

## 🛠️ Development

### Local Development Setup

1. **Backend Development**:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend Development**:
```bash
npm install
npm run dev
```

3. **Start Prometheus & Grafana**:
```bash
docker-compose up prometheus grafana
```

### Adding New Query Patterns

Edit `backend/main.py` in the `PrometheusQueryTranslator` class:

```python
self.query_patterns = {
    r'your pattern': 'your_promql_query',
    # ... existing patterns
}
```

## 🔍 API Reference

### POST /query

Query metrics using natural language.

**Request:**
```json
{
  "query": "What's the average CPU usage?"
}
```

**Response:**
```json
{
  "natural_language_response": "The CPU usage is currently 45.2%",
  "promql_query": "rate(cpu_usage_percent[5m])",
  "raw_data": {...},
  "grafana_url": "http://localhost:3000/explore?...",
  "execution_time": 0.123
}
```

### GET /health

Health check endpoint.

### GET /metrics

Prometheus metrics for the AI agent itself.

## 🐳 Docker Services

- **fastapi-app**: Main AI agent API
- **prometheus**: Metrics collection and storage
- **grafana**: Visualization and dashboards
- **frontend**: React web interface

## 🔧 Troubleshooting

### Common Issues

1. **"Unable to connect to Prometheus"**
   - Ensure Prometheus is running: `docker-compose ps`
   - Check logs: `docker-compose logs prometheus`

2. **"No data found for query"**
   - Wait a few minutes for metrics to be collected
   - Check if your app is exposing metrics at `/metrics`

3. **Frontend can't connect to API**
   - Verify API is running: `curl http://localhost:8000/health`
   - Check CORS settings if accessing from different domain

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi-app
```

## 🚀 Production Deployment

For production use:

1. **Security**: Add authentication and authorization
2. **SSL/TLS**: Use HTTPS with reverse proxy (nginx/traefik)
3. **Monitoring**: Set up alerts for the AI agent itself
4. **Scaling**: Use container orchestration (Kubernetes)
5. **Backup**: Implement Prometheus data backup strategy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions and support:

- Create an issue on GitHub
- Check the troubleshooting section
- Review Docker logs for errors

---

Built with ❤️ for the DevOps and SRE community!
```
