#!/bin/bash

# SecureCart AI Fraud Detection System - Setup and Installation Script
# This script automates the setup process for development and production environments

set -e  # Exit on any error

# =============================================================================
# CONFIGURATION AND VARIABLES
# =============================================================================

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
INSTALL_FRONTEND=true
INSTALL_BACKEND=true
INSTALL_DATABASE=true
INSTALL_BLOCKCHAIN=false
SKIP_DEPENDENCIES=false
VERBOSE=false

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Colored output functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR: $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_system_requirements() {
    print_info "Checking system requirements..."

    local requirements_met=true

    # Check operating system
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Detected Linux operating system"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Detected macOS operating system"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        print_info "Detected Windows operating system"
    else
        print_warning "Unknown operating system: $OSTYPE"
    fi

    # Check required commands
    local required_commands=("git" "curl")

    if [ "$INSTALL_BACKEND" = true ]; then
        required_commands+=("python3" "pip3")
    fi

    if [ "$INSTALL_FRONTEND" = true ]; then
        required_commands+=("node" "npm")
    fi

    if [ "$INSTALL_DATABASE" = true ]; then
        required_commands+=("docker" "docker-compose")
    fi

    for cmd in "${required_commands[@]}"; do
        if command_exists "$cmd"; then
            print_success "$cmd is installed"
        else
            print_error "$cmd is not installed"
            requirements_met=false
        fi
    done

    # Check Python version
    if [ "$INSTALL_BACKEND" = true ] && command_exists python3; then
        local python_version=$(python3 --version 2>&1 | cut -d" " -f2)
        local python_major=$(echo "$python_version" | cut -d"." -f1)
        local python_minor=$(echo "$python_version" | cut -d"." -f2)

        if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 8 ]; then
            print_success "Python version $python_version is supported"
        else
            print_error "Python 3.8+ is required (found $python_version)"
            requirements_met=false
        fi
    fi

    # Check Node.js version
    if [ "$INSTALL_FRONTEND" = true ] && command_exists node; then
        local node_version=$(node --version | sed 's/v//')
        local node_major=$(echo "$node_version" | cut -d"." -f1)

        if [ "$node_major" -ge 16 ]; then
            print_success "Node.js version $node_version is supported"
        else
            print_error "Node.js 16+ is required (found $node_version)"
            requirements_met=false
        fi
    fi

    if [ "$requirements_met" = false ]; then
        print_error "System requirements not met. Please install missing dependencies."
        exit 1
    fi

    print_success "All system requirements are met"
}

# Create project directories
create_directories() {
    print_info "Creating project directories..."

    local directories=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/models"
        "$PROJECT_ROOT/backups"
        "$PROJECT_ROOT/uploads"
        "$PROJECT_ROOT/static"
        "$PROJECT_ROOT/tests/unit"
        "$PROJECT_ROOT/tests/integration"
        "$PROJECT_ROOT/docs/api"
        "$PROJECT_ROOT/docker/nginx"
        "$PROJECT_ROOT/docker/grafana/dashboards"
        "$PROJECT_ROOT/docker/grafana/datasources"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
    done
}

# Setup environment configuration
setup_environment() {
    print_info "Setting up environment configuration..."

    # Copy environment template if .env doesn't exist
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success "Created .env file from template"
            print_warning "Please review and update the .env file with your specific configuration"
        else
            print_error ".env.example file not found"
            return 1
        fi
    else
        print_info ".env file already exists"
    fi

    # Generate secure secrets if they're still defaults
    if grep -q "your-secret-key-change-in-production" "$PROJECT_ROOT/.env"; then
        local secret_key=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/your-secret-key-change-in-production-must-be-at-least-32-characters-long/$secret_key/" "$PROJECT_ROOT/.env"
        print_success "Generated secure SECRET_KEY"
    fi

    if grep -q "jwt-secret-key-change-in-production" "$PROJECT_ROOT/.env"; then
        local jwt_key=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/jwt-secret-key-change-in-production-must-be-at-least-32-characters/$jwt_key/" "$PROJECT_ROOT/.env"
        print_success "Generated secure JWT_SECRET_KEY"
    fi
}

# Install Python dependencies
install_python_dependencies() {
    print_info "Installing Python dependencies..."

    cd "$PROJECT_ROOT"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Created virtual environment"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt
        print_success "Installed Python dependencies"
    else
        print_error "backend/requirements.txt not found"
        return 1
    fi

    # Install development dependencies if in development mode
    if [ "$ENVIRONMENT" = "development" ] && [ -f "backend/requirements-dev.txt" ]; then
        pip install -r backend/requirements-dev.txt
        print_success "Installed development dependencies"
    fi
}

# Install Node.js dependencies
install_node_dependencies() {
    print_info "Installing Node.js dependencies..."

    cd "$PROJECT_ROOT"

    if [ -f "package.json" ]; then
        # Use npm ci for faster, reliable installations
        if [ -f "package-lock.json" ]; then
            npm ci
        else
            npm install
        fi
        print_success "Installed Node.js dependencies"
    else
        print_error "package.json not found"
        return 1
    fi
}

# Setup database
setup_database() {
    print_info "Setting up database..."

    if [ "$ENVIRONMENT" = "development" ]; then
        # Use SQLite for development
        print_info "Using SQLite database for development"

        # Initialize database
        cd "$PROJECT_ROOT"
        source venv/bin/activate
        python -c "
from backend.database_models import DatabaseConfig
config = DatabaseConfig()
config.create_tables()
print('Database tables created successfully')
"
        print_success "Database initialized"

    else
        # Use Docker for PostgreSQL in production/staging
        print_info "Starting PostgreSQL with Docker..."

        cd "$PROJECT_ROOT"
        docker-compose up -d database redis

        # Wait for database to be ready
        print_info "Waiting for database to be ready..."
        timeout=60
        counter=0

        while [ $counter -lt $timeout ]; do
            if docker-compose exec -T database pg_isready -U postgres >/dev/null 2>&1; then
                print_success "Database is ready"
                break
            fi
            sleep 2
            counter=$((counter + 2))
        done

        if [ $counter -ge $timeout ]; then
            print_error "Database startup timeout"
            return 1
        fi

        # Initialize database tables
        source venv/bin/activate
        export DATABASE_URL="postgresql://postgres:secure_password_change_me@localhost:5432/securecart_fraud_detection"
        python -c "
from backend.database_models import DatabaseConfig
config = DatabaseConfig()
config.create_tables()
print('Database tables created successfully')
"
        print_success "Database initialized with PostgreSQL"
    fi
}

# Setup blockchain (optional)
setup_blockchain() {
    print_info "Setting up blockchain development environment..."

    cd "$PROJECT_ROOT"

    # Start Ganache using Docker
    docker-compose --profile blockchain up -d ganache

    # Wait for Ganache to be ready
    print_info "Waiting for Ganache to be ready..."
    timeout=30
    counter=0

    while [ $counter -lt $timeout ]; do
        if curl -s http://localhost:8545 >/dev/null 2>&1; then
            print_success "Ganache blockchain is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done

    if [ $counter -ge $timeout ]; then
        print_error "Ganache startup timeout"
        return 1
    fi

    # Deploy smart contracts
    source venv/bin/activate
    python -c "
from backend.blockchain_integration import BlockchainIntegration
blockchain = BlockchainIntegration('http://localhost:8545', 'development')
print('Blockchain integration initialized')
"
    print_success "Blockchain environment setup complete"
}

# Build frontend
build_frontend() {
    print_info "Building frontend application..."

    cd "$PROJECT_ROOT"

    if [ "$ENVIRONMENT" = "production" ]; then
        npm run build
        print_success "Frontend built for production"
    else
        print_info "Skipping frontend build for development (will run in dev mode)"
    fi
}

# Setup ML models
setup_ml_models() {
    print_info "Setting up ML models..."

    cd "$PROJECT_ROOT"
    source venv/bin/activate

    # Create models directory
    mkdir -p models

    # Initialize and train initial model
    python -c "
from backend.ml_fraud_detection import FraudDetectionSystem
import os

# Create sample training data and train model
fraud_system = FraudDetectionSystem()
fraud_system.create_sample_training_data()
fraud_system.train_model()
print('ML model trained and saved successfully')
"
    print_success "ML models initialized"
}

# Setup monitoring
setup_monitoring() {
    print_info "Setting up monitoring and logging..."

    cd "$PROJECT_ROOT"

    # Create log rotation configuration
    cat > "logs/logrotate.conf" << EOF
$PROJECT_ROOT/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
}
EOF

    # Setup monitoring with Docker (optional)
    if [ "$ENVIRONMENT" != "development" ]; then
        docker-compose --profile monitoring up -d prometheus grafana
        print_success "Monitoring stack started"
    fi

    print_success "Monitoring and logging configured"
}

# Run tests
run_tests() {
    print_info "Running tests..."

    cd "$PROJECT_ROOT"
    source venv/bin/activate

    # Backend tests
    if command_exists pytest; then
        pytest tests/ -v --cov=backend --cov-report=html
        print_success "Backend tests completed"
    else
        print_warning "pytest not found, skipping backend tests"
    fi

    # Frontend tests
    if [ -f "package.json" ] && npm list jest >/dev/null 2>&1; then
        npm test -- --coverage --watchAll=false
        print_success "Frontend tests completed"
    else
        print_warning "Jest not found, skipping frontend tests"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    cd "$PROJECT_ROOT"

    # Check if backend can start
    source venv/bin/activate
    timeout 10s python backend/app.py --check-config >/dev/null 2>&1 && \
        print_success "Backend configuration is valid" || \
        print_warning "Backend configuration check failed"

    # Check if database is accessible
    if [ "$ENVIRONMENT" = "development" ]; then
        [ -f "securecart_fraud_detection.db" ] && \
            print_success "SQLite database file exists" || \
            print_warning "SQLite database file not found"
    else
        docker-compose exec -T database pg_isready -U postgres >/dev/null 2>&1 && \
            print_success "PostgreSQL database is accessible" || \
            print_warning "PostgreSQL database is not accessible"
    fi

    # Check if required directories exist
    for dir in logs models static; do
        [ -d "$dir" ] && \
            print_success "Directory $dir exists" || \
            print_warning "Directory $dir not found"
    done

    print_success "Installation verification completed"
}

# Display usage information
show_usage() {
    cat << EOF
SecureCart AI Fraud Detection System - Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV     Set environment (development|testing|production) [default: development]
    --no-frontend            Skip frontend installation
    --no-backend             Skip backend installation
    --no-database            Skip database setup
    --blockchain             Install blockchain components
    --skip-deps              Skip dependency installation
    --skip-tests             Skip running tests
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message

EXAMPLES:
    $0                                    # Full development setup
    $0 -e production --blockchain         # Production setup with blockchain
    $0 --no-frontend --no-database        # Backend only setup
    $0 --skip-deps --skip-tests           # Quick setup without deps and tests

ENVIRONMENTS:
    development    Local development with SQLite
    testing        Testing environment with in-memory database
    production     Production setup with PostgreSQL and Redis

REQUIREMENTS:
    - Python 3.8+
    - Node.js 16+
    - Docker and Docker Compose (for production)
    - Git

For more information, see README.md or docs/setup.md
EOF
}

# Main installation function
main() {
    print_info "Starting SecureCart AI Fraud Detection System setup..."
    print_info "Environment: $ENVIRONMENT"
    print_info "Log file: $LOG_FILE"

    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"

    # Check system requirements
    if [ "$SKIP_DEPENDENCIES" = false ]; then
        check_system_requirements
    fi

    # Create project structure
    create_directories

    # Setup environment configuration
    setup_environment

    # Install dependencies
    if [ "$SKIP_DEPENDENCIES" = false ]; then
        if [ "$INSTALL_BACKEND" = true ]; then
            install_python_dependencies
        fi

        if [ "$INSTALL_FRONTEND" = true ]; then
            install_node_dependencies
        fi
    fi

    # Setup database
    if [ "$INSTALL_DATABASE" = true ]; then
        setup_database
    fi

    # Setup blockchain (if requested)
    if [ "$INSTALL_BLOCKCHAIN" = true ]; then
        setup_blockchain
    fi

    # Build frontend
    if [ "$INSTALL_FRONTEND" = true ]; then
        build_frontend
    fi

    # Setup ML models
    if [ "$INSTALL_BACKEND" = true ]; then
        setup_ml_models
    fi

    # Setup monitoring
    setup_monitoring

    # Run tests (if not skipped)
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi

    # Verify installation
    verify_installation

    print_success "Setup completed successfully!"

    # Display next steps
    cat << EOF

🎉 SecureCart AI Fraud Detection System is now ready!

NEXT STEPS:
1. Review and update .env file with your configuration
2. Start the development server:

   Backend:  source venv/bin/activate && python backend/app.py
   Frontend: npm start

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api
   - Admin Dashboard: http://localhost:3000/admin

4. Default credentials:
   - Admin: admin / admin123
   - Analyst: analyst / analyst123
   - User: testuser / user123

DOCUMENTATION:
- API Documentation: http://localhost:5000/docs
- Setup Guide: docs/setup.md
- User Manual: docs/user-guide.md

SUPPORT:
- GitHub Issues: https://github.com/your-repo/issues
- Documentation: docs/
- Email: support@securecart.com

Happy coding! 🚀
EOF
}

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --no-frontend)
            INSTALL_FRONTEND=false
            shift
            ;;
        --no-backend)
            INSTALL_BACKEND=false
            shift
            ;;
        --no-database)
            INSTALL_DATABASE=false
            shift
            ;;
        --blockchain)
            INSTALL_BLOCKCHAIN=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPENDENCIES=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|testing|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_info "Valid environments: development, testing, production"
    exit 1
fi

# Run main function
main "$@"
