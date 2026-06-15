---
icon: lucide/file-code
---

# Docker Compose

Docker Compose is the recommended way to run Downtify for persistent home-server setups. It makes updates, backups and configuration changes easy.

## Minimal setup

Create a `docker-compose.yml` file:

```yaml
services:
  downtify:
    container_name: downtify
    image: ghcr.io/securednodedynamics/downtify:latest
    ports:
      - '8000:8000'
    volumes:
      - ./downloads:/downloads
      - downtify_data:/data
    restart: unless-stopped

volumes:
  downtify_data:
```

Start it:

```bash
docker compose up -d
```

Open **[http://localhost:8000](http://localhost:8000)**.

## Custom port

If port 8000 is already in use, map a different host port and set the `DOWNTIFY_PORT` environment variable so the container listens on the same port internally:

```yaml
services:
  downtify:
    image: ghcr.io/securednodedynamics/downtify:latest
    ports:
      - '9090:30321'
    environment:
      - DOWNTIFY_PORT=30321
    volumes:
      - ./downloads:/downloads
      - downtify_data:/data
    restart: unless-stopped
```

## With custom DNS (recommended)

Some ISPs and corporate networks block YouTube. Adding explicit DNS resolvers improves reliability:

```yaml
services:
  downtify:
    image: ghcr.io/securednodedynamics/downtify:latest
    ports:
      - '8000:8000'
    volumes:
      - ./downloads:/downloads
      - downtify_data:/data
    dns:
      - 1.1.1.1
      - 1.0.0.1
    restart: unless-stopped
```

## Updating

```bash
docker compose pull
docker compose up -d
```

Your music and settings are preserved in the volumes.

## Troubleshooting compose errors

If you see `mapping key "services" already defined`, your compose file has
more than one top-level `services:` block. Keep one `services:` block and put
the `downtify:` service under it. Do not paste multiple examples into the same
file unless you merge them first.

If you see `pull access denied for downtify`, Docker is trying to pull an image
named only `downtify`. Set the image explicitly:

```yaml
services:
  downtify:
    image: ghcr.io/securednodedynamics/downtify:latest
```

The `lscr.io/v2` error usually comes from another app/image registry check in
the host manager. Downtify's image is hosted on GitHub Container Registry at
`ghcr.io/securednodedynamics/downtify:latest`.

## Volumes

| Path inside the compose file | Purpose |
|------------------------------|---------|
| `./downloads:/downloads` | Downloaded audio files (local directory) |
| `downtify_data:/data` | Application database and settings (named volume) |

You can replace the named volume with a local path (`./data:/data`) if you prefer to manage it yourself.
