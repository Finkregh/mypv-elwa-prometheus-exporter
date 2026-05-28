# my-PV AC ELWA Prometheus Exporter

A Python application that exports my-PV AC ELWA device statistics as Prometheus metrics for monitoring and visualization.

## Features

- Export my-PV AC ELWA device metrics in Prometheus format
- Support for multiple devices
- HTTP server mode for continuous Prometheus scraping
- One-time export mode for batch metrics collection
- Configurable logging levels and output destinations
- Docker container support for easy deployment

## Installation

### From Source

```bash
# Clone the repository
git clone https://git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter.git
cd mypv-ac-elwa-exporter

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Using Docker

Pull the pre-built image:

```bash
docker pull git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter:latest
```

Or build locally:

```bash
docker build -t mypv-elwa-exporter .
```

## Usage

### Command Line

#### Test Connection

```bash
mypv-elwa-prometheus-exporter test-connection --url http://192.168.178.125
```

#### HTTP Server Mode (Recommended for Prometheus)

Start an HTTP server that continuously serves metrics for Prometheus scraping:

```bash
mypv-elwa-prometheus-exporter serve --url http://192.168.178.125 --port 8000
```

Multiple devices:
```bash
mypv-elwa-prometheus-exporter serve --url "http://192.168.178.125,http://192.168.178.126" --port 8000
```

#### Export Mode (One-time)

Export metrics once to stdout or file:

```bash
# To stdout
mypv-elwa-prometheus-exporter export --url http://192.168.178.125

# To file
mypv-elwa-prometheus-exporter export --url http://192.168.178.125 --output metrics.txt
```

### Docker

#### Using Docker Run

```bash
# HTTP server mode
docker run -d --name mypv-exporter \
  -p 8000:8000 \
  -e MYPVELWAEXPORTER_SERVE_URL=http://192.168.178.125 \
  git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter:latest

# Export mode (one-time)
docker run --rm \
  -e MYPVELWAEXPORTER_EXPORT_URL=http://192.168.178.125 \
  git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter:latest \
  mypv-elwa-prometheus-exporter export
```

#### Using Docker Compose

Copy the `example-config.env` file and customize it:

```bash
cp example-config.env .env
# Edit .env with your device URL(s)
```

Start with docker-compose:

```bash
docker-compose up -d
```

The metrics will be available at `http://localhost:8000/metrics`.

## Configuration

### Environment Variables

The application uses environment variables with the prefix `MYPVELWAEXPORTER_`:

#### Server Mode (`serve` command)
- `MYPVELWAEXPORTER_SERVE_URL`: Device URL(s), comma-separated for multiple devices
- `MYPVELWAEXPORTER_SERVE_PORT`: HTTP server port (default: 8000)
- `MYPVELWAEXPORTER_SERVE_LOG_LEVEL`: Logging level (default: INFO)
- `MYPVELWAEXPORTER_SERVE_LOG_FILE`: Optional log file path

#### Export Mode (`export` command)
- `MYPVELWAEXPORTER_EXPORT_URL`: Device URL(s), comma-separated for multiple devices
- `MYPVELWAEXPORTER_EXPORT_OUTPUT`: Optional output file path (default: stdout)
- `MYPVELWAEXPORTER_EXPORT_LOG_LEVEL`: Logging level (default: INFO)

### Configuration File

You can also use the provided `example-config.env` as a template:

```bash
# Copy and edit the configuration
cp example-config.env my-config.env

# Use with Docker
docker-compose --env-file my-config.env up -d

# Or source it for local usage
source my-config.env
mypv-elwa-prometheus-exporter serve
```

## Prometheus Configuration

Add the exporter to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'mypv-elwa'
    static_configs:
      - targets: ['localhost:8000']  # Adjust host and port as needed
    scrape_interval: 30s
    metrics_path: /metrics
```

## Metrics

The exporter provides the following metrics:

- **Device Information**: Device model, firmware version, serial number
- **Power Metrics**: ELWA power consumption, grid power, solar power
- **Temperature Metrics**: Temperature sensors (T1, T2)
- **Electrical System**: Voltage, frequency, power factor
- **Device Health**: Connection status, error codes

All metrics are labeled with device instance information for multi-device setups.

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linting
uv run black .
uv run mypy .
```

### Building

```bash
# Build package
uv build

# Build Docker image
docker build -t mypv-elwa-exporter .
```

## Docker Deployment

### Production Deployment

1. **Create configuration file**:
   ```bash
   cp example-config.env production.env
   # Edit production.env with your actual device URLs
   ```

2. **Deploy with docker-compose**:
   ```bash
   docker-compose --env-file production.env up -d
   ```

3. **Check logs**:
   ```bash
   docker-compose logs -f mypv-elwa-exporter
   ```

4. **Health check**:
   ```bash
   curl http://localhost:8000/metrics
   ```

### Integration with Monitoring Stack

The exporter integrates well with the standard Prometheus + Grafana monitoring stack:

```yaml
# docker-compose.yml example for full monitoring stack
version: '3.8'

services:
  mypv-elwa-exporter:
    image: git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter:latest
    environment:
      - MYPVELWAEXPORTER_SERVE_URL=http://192.168.178.125
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    networks:
      - monitoring

networks:
  monitoring:
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Open an issue on the [project repository](https://git.h.oluflorenzen.de/finkregh/mypv-ac-elwa-exporter/issues)
- Check the logs with `--log-level DEBUG` for troubleshooting
