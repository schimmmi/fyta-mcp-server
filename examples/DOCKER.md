# FYTA API Wrapper - Docker Deployment

Complete guide for running FYTA API wrappers in Docker containers.

## 📋 Prerequisites

- Docker 20.10 or higher
- Docker Compose 2.0 or higher
- FYTA account credentials

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd /path/to/fyta-mcp-server/examples

# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Choose Your Deployment

#### Option A: Basic API Wrapper (Default)

```bash
# Build and start
docker-compose up -d fyta-api

# Check status
docker-compose ps

# View logs
docker-compose logs -f fyta-api

# Test
curl http://localhost:5000/health
curl http://localhost:5000/api/events
```

#### Option B: API Wrapper with Webhooks

```bash
# Set webhook URL in .env
echo "WEBHOOK_URL=https://your-n8n.com/webhook/fyta" >> .env

# Start with webhooks profile
docker-compose --profile webhooks up -d

# This starts:
# - fyta-api-webhooks (port 5001)
# - fyta-cron (triggers webhook push every 5 minutes)

# Test webhook push
curl -X POST http://localhost:5001/api/events/push
```

#### Option C: API Wrapper with MQTT

```bash
# Start with MQTT profile
docker-compose --profile mqtt up -d

# This starts:
# - fyta-api-mqtt (port 5002)
# - mosquitto MQTT broker (ports 1883, 9001)
# - fyta-mqtt-cron (publishes to MQTT every 5 minutes)

# Test MQTT publish
curl -X POST http://localhost:5002/api/events/mqtt

# Subscribe to MQTT topics
docker exec -it fyta-mosquitto mosquitto_sub -t "homeassistant/sensor/fyta/#" -v
```

## 📦 Services Overview

| Service | Port | Description | Profile |
|---------|------|-------------|---------|
| `fyta-api` | 5000 | Basic REST API | default |
| `fyta-api-webhooks` | 5001 | API with webhook push | webhooks |
| `fyta-api-mqtt` | 5002 | API with MQTT publishing | mqtt |
| `mosquitto` | 1883, 9001 | MQTT broker | mqtt |
| `fyta-cron` | - | Webhook push scheduler | webhooks |
| `fyta-mqtt-cron` | - | MQTT publish scheduler | mqtt |

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```bash
# Required
FYTA_EMAIL=your-email@example.com
FYTA_PASSWORD=your-password

# Webhooks (optional)
WEBHOOK_URL=https://your-webhook-url.com

# MQTT (optional)
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=homeassistant/sensor/fyta
```

### Docker Compose Profiles

Profiles allow running different variants without starting all services:

```bash
# Default (basic API only)
docker-compose up -d

# With webhooks
docker-compose --profile webhooks up -d

# With MQTT
docker-compose --profile mqtt up -d

# All services
docker-compose --profile webhooks --profile mqtt up -d
```

### Port Mapping

Change ports in `docker-compose.yml`:

```yaml
services:
  fyta-api:
    ports:
      - "8080:5000"  # Change 5000 to 8080
```

### Worker Configuration

Adjust Gunicorn workers for performance:

```yaml
command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 120 examples.api_wrapper:app
#                                               ^^^ Change worker count
```

Recommended workers: 2-4 × CPU cores

## 📊 Monitoring

### Health Checks

All API containers have built-in health checks:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect fyta-api-wrapper | grep -A 10 Health
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fyta-api

# Last 100 lines
docker-compose logs --tail 100 fyta-api

# With timestamps
docker-compose logs -f -t fyta-api
```

### Resource Usage

```bash
# Container stats
docker stats fyta-api-wrapper

# Disk usage
docker system df
```

## 🔄 Updating

### Update Images

```bash
# Pull latest changes
cd /path/to/fyta-mcp-server
git pull

# Rebuild containers
cd examples
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d
```

### Update Single Service

```bash
# Rebuild specific service
docker-compose build fyta-api

# Recreate container
docker-compose up -d --force-recreate fyta-api
```

## 🛠️ Maintenance

### Start/Stop Services

```bash
# Start all
docker-compose start

# Stop all
docker-compose stop

# Restart all
docker-compose restart

# Start specific service
docker-compose start fyta-api
```

### Remove Containers

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all
```

### Clean Up

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

## 🔒 Production Deployment

### 1. Use Secrets for Credentials

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  fyta-api:
    extends:
      file: docker-compose.yml
      service: fyta-api
    environment:
      - FYTA_EMAIL=${FYTA_EMAIL}
      - FYTA_PASSWORD=${FYTA_PASSWORD}
    secrets:
      - fyta_credentials

secrets:
  fyta_credentials:
    file: ./secrets/fyta_credentials.txt
```

### 2. Enable HTTPS

Use reverse proxy (nginx/Traefik):

```yaml
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - fyta-api
```

### 3. Enable MQTT Authentication

```bash
# Create password file
docker exec -it fyta-mosquitto mosquitto_passwd -c /mosquitto/config/passwd username

# Update mosquitto.conf
allow_anonymous false
password_file /mosquitto/config/passwd
```

### 4. Resource Limits

```yaml
services:
  fyta-api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 5. Auto-Restart Policy

```yaml
services:
  fyta-api:
    restart: always  # or: unless-stopped, on-failure
```

## 🧪 Testing

### Test Basic API

```bash
# Health check
curl http://localhost:5000/health

# Get plants
curl http://localhost:5000/api/plants | jq

# Get events
curl http://localhost:5000/api/events | jq

# Diagnose plant
curl http://localhost:5000/api/diagnose/108009 | jq
```

### Test Webhooks

```bash
# Trigger webhook push
curl -X POST http://localhost:5001/api/events/push

# Check cron logs
docker-compose logs fyta-cron
```

### Test MQTT

```bash
# Subscribe to all topics
docker exec -it fyta-mosquitto mosquitto_sub -t "homeassistant/sensor/fyta/#" -v

# In another terminal, trigger publish
curl -X POST http://localhost:5002/api/events/mqtt

# Test with mosquitto_pub
docker exec -it fyta-mosquitto mosquitto_pub -t "test" -m "hello"
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs fyta-api

# Check if port is already in use
sudo lsof -i :5000

# Rebuild without cache
docker-compose build --no-cache fyta-api
```

### API Returns Errors

```bash
# Check environment variables
docker-compose exec fyta-api env | grep FYTA

# Test FYTA credentials
docker-compose exec fyta-api python -c "
from src.fyta_mcp_server.client import FytaClient
import asyncio
import os

async def test():
    client = FytaClient(os.getenv('FYTA_EMAIL'), os.getenv('FYTA_PASSWORD'))
    await client.login()
    print('Login successful!')

asyncio.run(test())
"
```

### MQTT Connection Failed

```bash
# Check mosquitto is running
docker-compose ps mosquitto

# Check mosquitto logs
docker-compose logs mosquitto

# Test connection
docker exec -it fyta-api-mqtt nc -zv mosquitto 1883
```

### Cron Jobs Not Running

```bash
# Check cron container logs
docker-compose logs fyta-cron

# Check crontab
docker exec fyta-cron cat /etc/crontabs/root

# Verify service is reachable
docker exec fyta-cron curl http://fyta-api-webhooks:5000/health
```

### High Memory Usage

```bash
# Check stats
docker stats

# Reduce worker count in docker-compose.yml
command: gunicorn --bind 0.0.0.0:5000 --workers 2 ...

# Restart
docker-compose restart fyta-api
```

## 🌐 Integration Examples

### Home Assistant with Docker

```yaml
# Add to Home Assistant configuration.yaml
sensor:
  - platform: rest
    name: FYTA Events
    resource: http://fyta-api:5000/api/events  # Use container name
    method: GET
    value_template: "{{ value_json.event_count }}"
```

### n8n with Docker

```yaml
# Add to n8n docker-compose.yml
services:
  n8n:
    networks:
      - fyta-network  # Same network as FYTA API

networks:
  fyta-network:
    external: true
```

Then in n8n workflow:
- HTTP Request URL: `http://fyta-api:5000/api/events`

## 📁 Directory Structure

```
examples/
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # Multi-service orchestration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .env                           # Your credentials (gitignored)
├── mosquitto.conf                 # MQTT broker config
└── DOCKER.md                      # This file
```

## 🔗 Useful Commands Reference

```bash
# View all containers
docker-compose ps

# Follow all logs
docker-compose logs -f

# Restart specific service
docker-compose restart fyta-api

# Execute command in container
docker-compose exec fyta-api bash

# View container resources
docker stats

# Validate compose file
docker-compose config

# Scale service (multiple instances)
docker-compose up -d --scale fyta-api=3
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Mosquitto Documentation](https://mosquitto.org/documentation/)

---

**Happy Dockerizing! 🐳🌱**
