# 🚀 Prism Analytics - Complete Deployment Guide

## Quick Start (Recommended)

### Option 1: One-Command Deployment
```bash
# Clone your repository
git clone <your-repo-url>
cd music-analytics-platform

# Make deployment script executable
chmod +x deploy.sh

# Deploy everything automatically
./deploy.sh
```

### Option 2: Manual Step-by-Step

#### Prerequisites
- Docker 20.10+ installed and running
- Docker Compose installed
- 4GB+ RAM available
- 2GB+ disk space

#### Step 1: Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Generate secure API key (Linux/Mac)
openssl rand -base64 32

# Edit .env file with your settings
nano .env
```

#### Step 2: Create Missing Frontend Files
```bash
# Create Tailwind config
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        prism: { black: '#1A1A1A', red: '#E50914', gray: '#333333', white: '#FFFFFF' }
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }
    }
  },
  plugins: []
}
EOF

# Create PostCSS config
cat > frontend/postcss.config.js << 'EOF'
module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}
EOF
```

#### Step 3: Build and Deploy
```bash
# Create directories
mkdir -p data/{raw,processed} reports/generated logs ssl

# Build and start services
docker-compose up -d --build

# Wait for services to start (2-3 minutes)
docker-compose logs -f

# Initialize database
docker-compose exec backend python -c "
from models.database import init_database
init_database()
print('✅ Database initialized!')
"

# Generate sample data (optional)
docker-compose exec backend python utils/config.py generate 12 5000
```

#### Step 4: Verify Deployment
```bash
# Check service status
docker-compose ps

# Test backend API
curl http://localhost:5000/health

# Test frontend
curl http://localhost:3000
```

## 🌐 Access Your Platform

Once deployed successfully:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Docs**: http://localhost:5000/api/v1/docs
- **Health Check**: http://localhost:5000/health

## 📧 Email Configuration

To enable report email delivery, update your `.env` file:

```env
# Gmail Example
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # NOT your regular password!
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Prism Analytics
```

### Gmail Setup:
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App passwords
3. Use the generated app password (16 characters) in `.env`

## 📊 Upload Data Files

### Supported Formats
- CSV files (`.csv`)
- Excel files (`.xlsx`, `.xls`)
- Tab-separated files (`.tsv`)

### Data Structure Examples

#### Spotify Streaming Data
```csv
ISRC,Artist Name,Track Name,Country,Streams,Date
USRC17607839,Taylor Swift,Anti-Hero,US,1234567,2024-01
GBUM71507078,Ed Sheeran,Shape of You,GB,567890,2024-01
```

#### Apple Music Data
```csv
Apple Identifier,Storefront Name,Streams,Subscription Type,Datestamp
1234567890,United States,45678,Premium,2024-01-15
```

### Upload Process
1. **Copy files** to `data/raw/` directory
2. **Organize by platform** (optional): `data/raw/spotify/`, `data/raw/apple/`
3. **Process files**:
   ```bash
   docker-compose exec backend python -c "
   from services.data_processor import MusicDataProcessor
   processor = MusicDataProcessor()
   result = processor.process_folder('/app/data/raw')
   print(f'✅ Processed: {result}')
   "
   ```

## 🔧 Management Commands

### Service Management
```bash
# View logs
./deploy.sh logs

# Restart services
./deploy.sh restart

# Stop everything
./deploy.sh stop

# Check status
./deploy.sh status

# Clean everything (DESTRUCTIVE!)
./deploy.sh clean
```

### Data Management
```bash
# Create backup
./deploy.sh backup

# Generate sample data
docker-compose exec backend python utils/config.py generate 12 10000

# Reset database
docker-compose exec backend python -c "
import os
os.remove('/app/data/music_analytics.db')
from models.database import init_database
init_database()
"
```

### Report Generation
```bash
# Generate Wrapped report via API
curl -X POST http://localhost:5000/reports/generate/wrapped \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "SAMPLE_TAYLOR_SWIFT_000",
    "year": 2024,
    "email": "artist@example.com"
  }'

# Generate monthly report
curl -X POST http://localhost:5000/reports/generate/monthly \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "SAMPLE_TAYLOR_SWIFT_000",
    "year": 2024,
    "month": 12
  }'
```

## 🎯 Using the Platform

### 1. Dashboard Overview
- View total streams, unique artists, platform distribution
- See trending artists with growth metrics
- Monitor weekly performance

### 2. Platform Analysis
- Compare performance across Spotify, Apple Music, YouTube, etc.
- Analyze market share and unique tracks per platform
- Track platform-specific growth

### 3. Report Builder
- Search for artists in your database
- Generate Spotify Wrapped-style annual reports
- Create monthly performance summaries
- Email reports directly to artists/labels

### 4. Artist Analytics
- Deep dive into individual artist performance
- View top tracks and platform breakdown
- Analyze geographic reach and growth trends

## 🔒 Production Deployment

### Security Checklist
- [ ] Change default API keys in `.env`
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall rules (ports 80, 443, 22 only)
- [ ] Set up regular backups
- [ ] Enable rate limiting
- [ ] Update email credentials

### SSL Setup (Production)
```bash
# Generate SSL certificates
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx.key -out ssl/nginx.crt

# Use production Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables (Production)
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@db:5432/music_analytics  # For scale
API_SECRET_KEY=GENERATE_SECURE_64_CHAR_KEY_HERE
SMTP_USERNAME=your-production-email@domain.com
SMTP_PASSWORD=your-app-password
```

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker
docker info
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend
```

#### Database Issues
```bash
# Reset database
rm data/music_analytics.db
docker-compose restart backend
```

#### File Processing Errors
```bash
# Check file permissions
ls -la data/raw/

# Test file reading
docker-compose exec backend python -c "
from utils.file_handlers import FileHandler
handler = FileHandler()
files = handler.discover_files('/app/data/raw')
print(f'Found {len(files)} files')
for file in files[:5]:
    print(f'  - {file}')
"
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limit in docker-compose.yml:
services:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 1g
```

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000
lsof -i :5000

# Change ports in docker-compose.yml if needed
```

### Performance Optimization

#### Database Performance
- For datasets > 1M records, consider PostgreSQL
- Add indexes for frequently queried columns
- Regular VACUUM and ANALYZE for SQLite

#### File Processing
- Process files in batches during off-peak hours
- Use SSD storage for better I/O performance
- Monitor disk space regularly

#### Memory Usage
- Default setup handles ~100K records efficiently
- For larger datasets, increase Docker memory limits
- Consider data partitioning for very large datasets

## 📈 Scaling Considerations

### When to Scale
- Database size > 10GB
- Concurrent users > 50
- File processing takes > 30 minutes
- Memory usage consistently > 80%

### Scaling Options
1. **Vertical Scaling**: Increase server resources
2. **Database Migration**: SQLite → PostgreSQL
3. **Caching**: Add Redis for performance
4. **Load Balancing**: Multiple backend instances
5. **CDN**: For static assets and reports

### Cloud Deployment
The platform is ready for deployment on:
- **AWS**: Use ECS/Fargate or EC2 with Docker
- **Google Cloud**: Cloud Run or GKE
- **Azure**: Container Instances or AKS
- **DigitalOcean**: App Platform or Droplets

## 📞 Support

### Getting Help
1. Check this deployment guide first
2. Review logs: `docker-compose logs`
3. Check GitHub issues
4. Contact: ces@precise.digital

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

**🎵 Built with ❤️ for the music industry**

*Prism Analytics - Turning music data into actionable insights*