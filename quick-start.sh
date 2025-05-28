#!/bin/bash
# quick-start.sh - Complete setup and deployment in one script

set -e

echo "🎵 PRISM ANALYTICS - QUICK START DEPLOYMENT"
echo "============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

# Function to create missing files
create_missing_files() {
    print_info "Creating missing configuration files..."
    
    # Create frontend Tailwind config
    cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        prism: { black: '#1A1A1A', red: '#E50914', gray: '#333333', white: '#FFFFFF' },
        gray: {
          50: '#f8f9fa', 100: '#f1f3f4', 200: '#e8eaed', 300: '#dadce0', 400: '#bdc1c6',
          500: '#9aa0a6', 600: '#80868b', 700: '#5f6368', 800: '#3c4043', 900: '#202124'
        }
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } }
      },
      boxShadow: {
        'prism': '0 4px 6px -1px rgba(229, 9, 20, 0.1), 0 2px 4px -1px rgba(229, 9, 20, 0.06)',
        'prism-lg': '0 10px 15px -3px rgba(229, 9, 20, 0.1), 0 4px 6px -2px rgba(229, 9, 20, 0.05)'
      }
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
    
    print_status "Frontend configuration files created"
}

# Function to setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
            
            # Generate secure API key
            if command -v openssl &> /dev/null; then
                API_KEY=$(openssl rand -base64 32)
                sed -i "s/your-secure-api-key-here/$API_KEY/" .env
                print_status "Generated secure API key"
            else
                print_warning "Please manually set API_SECRET_KEY in .env file"
            fi
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status ".env file already exists"
    fi
}

# Function to create directories
create_directories() {
    print_info "Creating necessary directories..."
    
    directories=(
        "data/raw"
        "data/processed"
        "reports/generated"
        "logs"
        "ssl"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_status "Directory structure created"
}

# Function to run pre-deployment checks
run_checks() {
    print_info "Running pre-deployment checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available."
        exit 1
    fi
    
    # Check ports
    if lsof -i :3000 &> /dev/null; then
        print_error "Port 3000 is already in use"
        exit 1
    fi
    
    if lsof -i :5000 &> /dev/null; then
        print_error "Port 5000 is already in use"
        exit 1
    fi
    
    print_status "All checks passed"
}

# Function to deploy services
deploy_services() {
    print_info "Deploying services with Docker Compose..."
    
    # Stop any existing services
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build and start services
    docker-compose up -d --build
    
    print_status "Services deployment initiated"
}

# Function to wait for services
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for backend
    print_info "Checking backend API..."
    for i in {1..60}; do
        if curl -s http://localhost:5000/health &> /dev/null; then
            print_status "Backend API is ready"
            break
        fi
        
        if [[ $i -eq 60 ]]; then
            print_error "Backend API failed to start within 2 minutes"
            echo ""
            echo "Backend logs:"
            docker-compose logs backend
            exit 1
        fi
        
        echo -n "."
        sleep 2
    done
    
    # Wait for frontend
    print_info "Checking frontend..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 &> /dev/null; then
            print_status "Frontend is ready"
            break
        fi
        
        if [[ $i -eq 60 ]]; then
            print_warning "Frontend may take longer to start (this is normal for first deployment)"
            break
        fi
        
        echo -n "."
        sleep 2
    done
    
    echo ""
}

# Function to initialize database
initialize_database() {
    print_info "Initializing database..."
    
    docker-compose exec -T backend python -c "
from models.database import init_database
init_database()
print('✅ Database schema initialized successfully!')
" || {
        print_error "Database initialization failed"
        echo ""
        echo "Backend logs:"
        docker-compose logs backend
        exit 1
    }
    
    print_status "Database initialized"
}

# Function to generate sample data
generate_sample_data() {
    echo ""
    read -p "Generate sample data for demonstration? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Generating sample data (this may take 1-2 minutes)..."
        
        docker-compose exec -T backend python -c "
from models.database import create_sample_data
create_sample_data()
print('✅ Sample data generated successfully!')
" || {
            print_warning "Sample data generation failed (optional feature)"
        }
        
        print_status "Sample data generated"
    else
        print_info "Skipping sample data generation"
    fi
}

# Function to show deployment summary
show_summary() {
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "======================"
    echo ""
    echo "📱 Your Prism Analytics Platform is ready:"
    echo ""
    echo "   🖥️  Frontend Dashboard: http://localhost:3000"
    echo "   🔌 Backend API:        http://localhost:5000"
    echo "   📚 API Health Check:   http://localhost:5000/health"
    echo ""
    echo "🚀 What you can do now:"
    echo ""
    echo "   1. 📊 Open http://localhost:3000 to access the dashboard"
    echo "   2. 🎵 Explore the music analytics interface"
    echo "   3. 📈 View platform performance and trending artists"
    echo "   4. 📄 Generate Spotify Wrapped-style reports"
    echo "   5. 📁 Upload your own music data to data/raw/"
    echo ""
    echo "🔧 Management commands:"
    echo ""
    echo "   ./deploy.sh logs     - View application logs"
    echo "   ./deploy.sh restart  - Restart all services"
    echo "   ./deploy.sh stop     - Stop all services"
    echo "   ./deploy.sh status   - Check service status"
    echo ""
    echo "📧 To enable email reports:"
    echo ""
    echo "   1. Edit .env file with your SMTP settings"
    echo "   2. Run: ./deploy.sh restart"
    echo ""
    echo "📖 For detailed documentation, see DEPLOYMENT_GUIDE.md"
    echo ""
    print_status "🎵 Prism Analytics is now running! 🎵"
    echo ""
}

# Main execution
main() {
    echo "Starting complete deployment process..."
    echo ""
    
    # Run all setup steps
    run_checks
    create_directories
    create_missing_files
    setup_environment
    deploy_services
    wait_for_services
    initialize_database
    generate_sample_data
    
    # Show final summary
    show_summary
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --no-sample    Skip sample data generation"
        echo ""
        echo "This script will:"
        echo "  1. Check system requirements"
        echo "  2. Create necessary files and directories"
        echo "  3. Setup environment configuration"
        echo "  4. Deploy services with Docker Compose"
        echo "  5. Initialize database"
        echo "  6. Optionally generate sample data"
        echo ""
        ;;
    "--no-sample")
        # Override the sample data function
        generate_sample_data() {
            print_info "Skipping sample data generation (--no-sample flag)"
        }
        main
        ;;
    *)
        main
        ;;
esac