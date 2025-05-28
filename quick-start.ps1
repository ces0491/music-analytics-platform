# quick-start.ps1 - PowerShell version for Windows
# Prism Analytics - Complete setup and deployment

Write-Host "🎵 PRISM ANALYTICS - QUICK START DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Function to print colored output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️ $Message" -ForegroundColor Blue }

# Function to create missing files
function Create-MissingFiles {
    Write-Info "Creating missing configuration files..."
    
    # Create frontend Tailwind config
    $tailwindConfig = @'
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
'@
    
    # Create PostCSS config
    $postcssConfig = @'
module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}
'@
    
    # Write files
    if (!(Test-Path "frontend")) { New-Item -ItemType Directory -Path "frontend" -Force | Out-Null }
    $tailwindConfig | Out-File -FilePath "frontend/tailwind.config.js" -Encoding UTF8
    $postcssConfig | Out-File -FilePath "frontend/postcss.config.js" -Encoding UTF8
    
    Write-Success "Frontend configuration files created"
}

# Function to setup environment
function Setup-Environment {
    Write-Info "Setting up environment..."
    
    if (!(Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Success "Created .env from .env.example"
            
            # Generate secure API key (PowerShell method)
            $apiKey = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
            (Get-Content ".env") -replace "your-secure-api-key-here", $apiKey | Set-Content ".env"
            Write-Success "Generated secure API key"
        } else {
            Write-Error ".env.example not found"
            exit 1
        }
    } else {
        Write-Success ".env file already exists"
    }
}

# Function to create directories
function Create-Directories {
    Write-Info "Creating necessary directories..."
    
    $directories = @(
        "data/raw",
        "data/processed", 
        "reports/generated",
        "logs",
        "ssl",
        "backups"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directory structure created"
}

# Function to run pre-deployment checks
function Test-Prerequisites {
    Write-Info "Running pre-deployment checks..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
        
        docker info | Out-Null
        Write-Success "Docker daemon is running"
    } catch {
        Write-Error "Docker is not installed or running. Please install Docker Desktop."
        Write-Host "Visit: https://docs.docker.com/docker-for-windows/install/" -ForegroundColor Blue
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose found: $composeVersion"
    } catch {
        try {
            $composeVersion = docker compose version
            Write-Success "Docker Compose (plugin) found: $composeVersion"
        } catch {
            Write-Error "Docker Compose is not available"
            exit 1
        }
    }
    
    # Check ports (PowerShell method)
    $port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    
    if ($port3000) {
        Write-Error "Port 3000 is already in use"
        exit 1
    }
    
    if ($port5000) {
        Write-Error "Port 5000 is already in use"
        exit 1
    }
    
    Write-Success "All checks passed"
}

# Function to deploy services
function Deploy-Services {
    Write-Info "Deploying services with Docker Compose..."
    
    # Stop any existing services
    docker-compose down --remove-orphans 2>$null
    
    # Build and start services
    docker-compose up -d --build
    
    Write-Success "Services deployment initiated"
}

# Function to wait for services
function Wait-ForServices {
    Write-Info "Waiting for services to be ready..."
    
    # Wait for backend
    Write-Info "Checking backend API..."
    $backendReady = $false
    for ($i = 1; $i -le 60; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend API is ready"
                $backendReady = $true
                break
            }
        } catch {
            # Ignore errors and continue waiting
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    if (!$backendReady) {
        Write-Error "Backend API failed to start within 2 minutes"
        Write-Host ""
        Write-Host "Backend logs:"
        docker-compose logs backend
        exit 1
    }
    
    # Wait for frontend
    Write-Info "Checking frontend..."
    $frontendReady = $false
    for ($i = 1; $i -le 60; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Success "Frontend is ready"
                $frontendReady = $true
                break
            }
        } catch {
            # Ignore errors and continue waiting
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    if (!$frontendReady) {
        Write-Warning "Frontend may take longer to start (this is normal for first deployment)"
    }
    
    Write-Host ""
}

# Function to initialize database
function Initialize-Database {
    Write-Info "Initializing database..."
    
    try {
        $initScript = @"
from models.database import init_database
init_database()
print('✅ Database schema initialized successfully!')
"@
        
        $initScript | docker-compose exec -T backend python
        Write-Success "Database initialized"
    } catch {
        Write-Error "Database initialization failed"
        Write-Host ""
        Write-Host "Backend logs:"
        docker-compose logs backend
        exit 1
    }
}

# Function to generate sample data
function Generate-SampleData {
    Write-Host ""
    $response = Read-Host "Generate sample data for demonstration? (y/n)"
    
    if ($response -match "^[Yy]$") {
        Write-Info "Generating sample data (this may take 1-2 minutes)..."
        
        try {
            $sampleScript = @"
from models.database import create_sample_data
create_sample_data()
print('✅ Sample data generated successfully!')
"@
            
            $sampleScript | docker-compose exec -T backend python
            Write-Success "Sample data generated"
        } catch {
            Write-Warning "Sample data generation failed (optional feature)"
        }
    } else {
        Write-Info "Skipping sample data generation"
    }
}

# Function to show deployment summary
function Show-Summary {
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Your Prism Analytics Platform is ready:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   🖥️  Frontend Dashboard: http://localhost:3000" -ForegroundColor White
    Write-Host "   🔌 Backend API:        http://localhost:5000" -ForegroundColor White
    Write-Host "   📚 API Health Check:   http://localhost:5000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 What you can do now:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   1. 📊 Open http://localhost:3000 to access the dashboard" -ForegroundColor White
    Write-Host "   2. 🎵 Explore the music analytics interface" -ForegroundColor White
    Write-Host "   3. 📈 View platform performance and trending artists" -ForegroundColor White
    Write-Host "   4. 📄 Generate Spotify Wrapped-style reports" -ForegroundColor White
    Write-Host "   5. 📁 Upload your own music data to data/raw/" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Management commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   docker-compose logs     - View application logs" -ForegroundColor White
    Write-Host "   docker-compose restart  - Restart all services" -ForegroundColor White
    Write-Host "   docker-compose stop     - Stop all services" -ForegroundColor White
    Write-Host "   docker-compose ps       - Check service status" -ForegroundColor White
    Write-Host ""
    Write-Host "📧 To enable email reports:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   1. Edit .env file with your SMTP settings" -ForegroundColor White
    Write-Host "   2. Run: docker-compose restart" -ForegroundColor White
    Write-Host ""
    Write-Success "🎵 Prism Analytics is now running! 🎵"
    Write-Host ""
}

# Main execution
function Main {
    Write-Host "Starting complete deployment process..." -ForegroundColor Cyan
    Write-Host ""
    
    try {
        Test-Prerequisites
        Create-Directories
        Create-MissingFiles
        Setup-Environment
        Deploy-Services
        Wait-ForServices
        Initialize-Database
        Generate-SampleData
        Show-Summary
    } catch {
        Write-Error "Deployment failed: $_"
        Write-Host ""
        Write-Host "For troubleshooting, run: docker-compose logs" -ForegroundColor Yellow
        exit 1
    }
}

# Handle command line arguments
switch ($args[0]) {
    "--help" {
        Write-Host "Usage: .\quick-start.ps1 [options]" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Options:" -ForegroundColor White
        Write-Host "  --help     Show this help message" -ForegroundColor White
        Write-Host ""
        Write-Host "This script will:" -ForegroundColor White
        Write-Host "  1. Check system requirements" -ForegroundColor White
        Write-Host "  2. Create necessary files and directories" -ForegroundColor White
        Write-Host "  3. Setup environment configuration" -ForegroundColor White
        Write-Host "  4. Deploy services with Docker Compose" -ForegroundColor White
        Write-Host "  5. Initialize database" -ForegroundColor White
        Write-Host "  6. Optionally generate sample data" -ForegroundColor White
        Write-Host ""
        break
    }
    default {
        Main
    }
}