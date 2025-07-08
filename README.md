# GiftManager - Docker Deployment

This Django application can be deployed using Docker and Docker Compose with persistent SQLite database storage.

## Quick Start

### Automated Setup (Recommended)

**For Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**For Windows:**
```cmd
setup.bat
```

### Manual Setup

1. **Clone the repository and navigate to the project directory**

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and update the values, especially:
   - `SECRET_KEY`: Generate a secure secret key
   - `ALLOWED_HOSTS`: Add your domain name
   - `DEBUG`: Set to `false` for production

3. **Create required directories**
   ```bash
   mkdir -p data static media
   ```

4. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

   Or for production with the production compose file:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Access the application**
   - Open your browser to `http://localhost:8000`
   - Default admin credentials: `admin` / `admin123`

## Persistent Data

The SQLite database is stored in the `./data` directory on your host machine, which is mounted as a volume in the container. This ensures your data persists across container restarts and updates.

## Directory Structure
```
./data/          # SQLite database (persistent)
./static/        # Static files (collected automatically)
./media/         # User uploaded files (if any)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Auto-generated (change for production) |
| `DEBUG` | Enable Django debug mode | `false` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,0.0.0.0` |
| `DATABASE_PATH` | Path to SQLite database in container | `/app/data/db.sqlite3` |

## Management Commands

To run Django management commands:

```bash
# Access the running container
docker exec -it giftmanager python manage.py <command>

# Examples:
docker exec -it giftmanager python manage.py createsuperuser
docker exec -it giftmanager python manage.py migrate
docker exec -it giftmanager python manage.py collectstatic
```

## Updating the Application

1. **Pull the latest code**
2. **Rebuild the image**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Backup

To backup your data:
```bash
# Backup the database
cp ./data/db.sqlite3 ./backup/db.sqlite3.$(date +%Y%m%d_%H%M%S)
```

## Logs

View application logs:
```bash
docker-compose logs -f web
```

## Security Notes

- Change the default `SECRET_KEY` in production
- Set `DEBUG=false` in production
- Update `ALLOWED_HOSTS` to include only your domain
- Change default admin password after first login
- Consider using a reverse proxy (nginx) for production deployments
