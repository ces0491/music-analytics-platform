#!/bin/bash
# deploy.sh - Complete deployment script for Music Analytics Platform

set -e  # Exit on any error

echo "🎵 PRISM ANALYTICS - MUSIC DATA INTELLIGENCE PLATFORM"
echo "======================================================"
echo "🚀 Starting deployment process..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if Docker is installed and running
check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_status "Docker is installed and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_info "Checking Docker Compose..."
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_status "Docker Compose is available"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    directories=(
        "data/raw"
        "data/processed"
        "reports/generated"
        "logs"
        "ssl"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
}

# Generate environment file if it doesn't exist
create_env_file() {
    if [ ! -f .env ]; then
        print_info "Creating environment file..."
        
        # Generate a secure API key
        API_KEY=$(openssl rand -base64 32)
        
        cat > .env << EOL
# API Configuration
API_SECRET_KEY=${API_KEY}
FLASK_ENV=production

# Database
DATABASE_URL=sqlite:///data/music_analytics.db

# Frontend
REACT_APP_API_URL=http://localhost:5000/api/v1

# Email Service (Configure these for email functionality)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Prism Analytics

# File Upload Limits
MAX_FILE_SIZE_MB=100
MAX_UPLOAD_SIZE=100MB

# Report Configuration
PDF_TIMEOUT_SECONDS=30

# Rate Limiting
RATE_LIMIT_PER_DAY=1000
RATE_LIMIT_PER_HOUR=100
EOL
        
        print_status "Environment file created with secure API key"
        print_warning "Please update email settings in .env file for email functionality"
    else
        print_status "Environment file already exists"
    fi
}

# Build and start services
deploy_services() {
    print_info "Building and starting services..."
    
    # Stop any existing services
    docker-compose down --remove-orphans
    
    # Build and start services
    docker-compose up -d --build
    
    print_status "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for backend
    print_info "Waiting for backend API..."
    for i in {1..30}; do
        if curl -s http://localhost:5000/health &> /dev/null; then
            print_status "Backend API is ready"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_error "Backend API failed to start"
            exit 1
        fi
        
        sleep 2
    done
    
    # Wait for frontend
    print_info "Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 &> /dev/null; then
            print_status "Frontend is ready"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_warning "Frontend may take longer to start (this is normal)"
            break
        fi
        
        sleep 2
    done
}

# Initialize database
initialize_database() {
    print_info "Initializing database..."
    
    docker-compose exec -T backend python -c "
from models.database import init_database
init_database()
print('Database initialized successfully!')
"
    
    print_status "Database initialized"
}

# Generate sample data
generate_sample_data() {
    print_info "Generating sample data for demonstration..."
    
    docker-compose exec -T backend python utils/config.py generate 12 10000
    
    print_status "Sample data generated"
}

# Display deployment summary
show_summary() {
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "======================"
    echo ""
    echo "📱 Access your Music Analytics Platform:"
    echo "   Frontend Dashboard: http://localhost:3000"
    echo "   Backend API:        http://localhost:5000"
    echo "   API Documentation:  http://localhost:5000/api/v1/docs"
    echo ""
    echo "🔧 Default Features Available:"
    echo "   ✅ Interactive Dashboard"
    echo "   ✅ Platform Analytics"
    echo "   ✅ Artist Profiles"
    echo "   ✅ Report Generation"
    echo "   ✅ Sample Data (10,000 records)"
    echo ""
    echo "📊 Key Features:"
    echo "   🎵 Multi-platform music analytics"
    echo "   📱 Responsive React dashboard"
    echo "   📄 PDF report generation (Spotify Wrapped style)"
    echo "   📧 Email delivery system"
    echo "   🔍 Real-time search and filtering"
    echo "   📈 Interactive charts and visualizations"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Open http://localhost:3000 in your browser"
    echo "   2. Explore the dashboard and analytics"
    echo "   3. Try generating a Wrapped report"
    echo "   4. Upload your own music data files to data/raw/"
    echo "   5. Configure email settings in .env for report delivery"
    echo ""
    echo "📖 For detailed documentation, see the project README"
    echo "🛠️ To customize, edit configuration files and restart services"
    echo ""
}

# Check logs if services fail
check_logs() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed. Checking logs..."
        echo ""
        echo "Backend logs:"
        docker-compose logs backend
        echo ""
        echo "Frontend logs:"
        docker-compose logs frontend
        exit 1
    fi
}

# Main deployment process
main() {
    echo "Starting deployment process..."
    echo ""
    
    # Pre-deployment checks
    check_docker
    check_docker_compose
    
    # Setup
    create_directories
    create_env_file
    
    # Deploy
    deploy_services
    wait_for_services
    
    # Initialize
    initialize_database
    
    # Optional: Generate sample data
    read -p "Generate sample data for demonstration? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        generate_sample_data
    fi
    
    # Success
    show_summary
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        print_info "Stopping all services..."
        docker-compose down
        print_status "All services stopped"
        ;;
    "restart")
        print_info "Restarting services..."
        docker-compose down
        docker-compose up -d
        wait_for_services
        print_status "Services restarted"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_status "System cleaned"
        fi
        ;;
    "backup")
        print_info "Creating backup..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="backups/backup_${timestamp}"
        mkdir -p "$backup_dir"
        
        # Backup database
        cp data/music_analytics.db "$backup_dir/" 2>/dev/null || true
        
        # Backup reports
        cp -r reports/generated "$backup_dir/" 2>/dev/null || true
        
        # Backup configuration
        cp .env "$backup_dir/" 2>/dev/null || true
        
        print_status "Backup created in $backup_dir"
        ;;
    "update")
        print_info "Updating application..."
        git pull origin main
        docker-compose down
        docker-compose up -d --build
        wait_for_services
        print_status "Application updated"
        ;;
    *)
        main
        ;;
esac