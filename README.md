# Gcore DDNS Solution

A simple Python script to keep your Gcore DNS records up to date with your public IP address.

## Features
- Supports multiple domains and zones.
- Supports wildcard records (`*.domain.com`).
- Configurable update interval (default: 5 minutes).
- Robust public IP detection using multiple services.

## Installation

1. Clone this repository (or copy the files).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example configuration:
   ```bash
   cp config.example.yaml config.yaml
   ```
2. Edit `config.yaml` and fill in your Gcore API key and desired records.

**Note:** If your API key contains special characters (like `$`), ensure it is wrapped in double quotes.

Example `config.yaml`:
```yaml
gcore_api_key: "your-api-key-here"
interval_minutes: 5
records:
  - zone: "aspwest.se"
    name: "*"
    type: "A"
    ttl: 300
  - zone: "aspwest.se"
    name: "@"
    type: "A"
    ttl: 300
```

## Usage

### Local Python
Run the script:
```bash
python gcore_ddns.py
```

### Docker

1. Build the image:
   ```bash
   docker build -t gcore-ddns .
   ```
2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

Alternatively, run with Docker directly:
```bash
docker run -d \
  --name gcore-ddns \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  gcore-ddns
```

## Notes
- The `name` field in the config should be the subdomain part (e.g., `home` for `home.aspwest.se`) or `@` for the root domain.
- Wildcards are supported as `*`.
