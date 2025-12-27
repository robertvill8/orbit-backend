#!/bin/bash

# ============================================================================
# RAILWAY DEPLOYMENT SCRIPT FOR ORBIT V3 BACKEND
# ============================================================================
# This script automates the deployment process to Railway.app
# Prerequisites:
#   - Railway CLI installed (npm i -g @railway/cli)
#   - Railway account logged in (railway login)
#   - Project linked (railway link)
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI not found!"
        echo "Install with: npm i -g @railway/cli"
        exit 1
    fi
    print_success "Railway CLI installed"
}

check_railway_auth() {
    if ! railway whoami &> /dev/null; then
        print_error "Not logged in to Railway!"
        echo "Login with: railway login"
        exit 1
    fi
    print_success "Railway authentication verified"
}

check_env_file() {
    if [ ! -f "$SCRIPT_DIR/.env.production" ]; then
        print_error ".env.production file not found!"
        echo "Create it from .env.production template"
        exit 1
    fi
    print_success ".env.production file found"
}

validate_env_vars() {
    print_info "Validating critical environment variables..."

    local required_vars=(
        "ANTHROPIC_API_KEY"
        "SECRET_KEY"
        "CORS_ORIGINS"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$SCRIPT_DIR/.env.production" || grep -q "^${var}=.*REPLACE.*" "$SCRIPT_DIR/.env.production" || grep -q "^${var}=.*XXX.*" "$SCRIPT_DIR/.env.production"; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing or invalid environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please update .env.production with actual values before deploying"
        exit 1
    fi

    print_success "All critical environment variables are set"
}

check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker is not running!"
        echo "Please start Docker Desktop and try again"
        exit 1
    fi
    print_success "Docker is running"
}

test_docker_build() {
    print_info "Testing Docker build locally..."

    cd "$SCRIPT_DIR"

    if docker build -t orbit-backend-test:latest . &> /dev/null; then
        print_success "Docker build successful"
        docker rmi orbit-backend-test:latest &> /dev/null
    else
        print_error "Docker build failed!"
        echo "Fix build errors before deploying"
        exit 1
    fi
}

link_railway_project() {
    print_info "Checking Railway project link..."

    if ! railway status &> /dev/null; then
        print_warning "Not linked to a Railway project"
        echo ""
        read -p "Do you want to link to an existing project or create a new one? (existing/new): " choice

        case $choice in
            existing)
                railway link
                ;;
            new)
                read -p "Enter project name: " project_name
                railway init --name "$project_name"
                ;;
            *)
                print_error "Invalid choice. Exiting."
                exit 1
                ;;
        esac
    fi

    print_success "Linked to Railway project: $(railway status | grep 'Project:' | awk '{print $2}')"
}

create_railway_services() {
    print_info "Checking required Railway services..."

    # Note: This requires manual creation via Railway dashboard
    # The CLI doesn't support creating databases yet

    echo ""
    echo "Please ensure the following services exist in your Railway project:"
    echo "  1. PostgreSQL database (with pgvector)"
    echo "  2. Redis database"
    echo ""
    read -p "Have you created these services? (y/n): " services_ready

    if [ "$services_ready" != "y" ]; then
        print_warning "Create services in Railway dashboard before continuing"
        echo "Visit: https://railway.app/dashboard"
        exit 1
    fi

    print_success "Railway services confirmed"
}

upload_env_vars() {
    print_info "Uploading environment variables to Railway..."

    cd "$SCRIPT_DIR"

    # Read .env.production and upload to Railway
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ $key =~ ^#.*$ ]] || [[ -z $key ]]; then
            continue
        fi

        # Remove leading/trailing whitespace and quotes
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs | sed 's/^["'\'']\(.*\)["'\'']$/\1/')

        # Skip service reference variables (Railway handles these)
        if [[ $value =~ \$\{\{.*\}\} ]]; then
            continue
        fi

        # Upload variable
        railway variables --set "$key=$value" &> /dev/null

    done < .env.production

    print_success "Environment variables uploaded"
}

deploy_to_railway() {
    print_info "Deploying to Railway..."

    cd "$SCRIPT_DIR"

    # Trigger deployment
    railway up --detach

    print_success "Deployment initiated"
}

wait_for_deployment() {
    print_info "Waiting for deployment to complete..."

    local max_wait=600  # 10 minutes
    local elapsed=0
    local interval=10

    while [ $elapsed -lt $max_wait ]; do
        if railway status | grep -q "ACTIVE"; then
            print_success "Deployment completed successfully!"
            return 0
        fi

        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    print_error "Deployment timeout!"
    echo "Check Railway dashboard for details"
    exit 1
}

run_migrations() {
    print_info "Running database migrations..."

    if railway run alembic upgrade head; then
        print_success "Migrations applied successfully"
    else
        print_warning "Migration failed - you may need to run manually"
        echo "Run: railway run alembic upgrade head"
    fi
}

get_deployment_url() {
    print_info "Fetching deployment URL..."

    local url=$(railway status | grep -oE 'https://[a-zA-Z0-9.-]+\.railway\.app' | head -1)

    if [ -z "$url" ]; then
        print_warning "Could not auto-detect URL"
        echo "Check Railway dashboard for your deployment URL"
    else
        print_success "Backend deployed to: $url"
        echo ""
        echo "Update your frontend with:"
        echo "  VITE_API_BASE_URL=${url}/api/v1"
        echo "  VITE_WS_URL=${url/https/wss}/ws"
    fi
}

verify_deployment() {
    print_info "Verifying deployment health..."

    local url=$(railway status | grep -oE 'https://[a-zA-Z0-9.-]+\.railway\.app' | head -1)

    if [ -z "$url" ]; then
        print_warning "Could not verify - URL not found"
        return
    fi

    # Wait a bit for service to be ready
    sleep 5

    # Check health endpoint
    if curl -f -s "${url}/health" > /dev/null; then
        print_success "Health check passed!"
    else
        print_warning "Health check failed - service may still be starting"
        echo "Manual check: curl ${url}/health"
    fi
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

main() {
    print_header "RAILWAY DEPLOYMENT - ORBIT V3 BACKEND"

    echo ""
    print_info "Starting pre-deployment checks..."
    echo ""

    # Pre-deployment checks
    check_railway_cli
    check_railway_auth
    check_docker_running
    check_env_file
    validate_env_vars

    echo ""
    print_info "Running build tests..."
    echo ""

    test_docker_build

    echo ""
    print_info "Configuring Railway project..."
    echo ""

    link_railway_project
    create_railway_services

    echo ""
    print_warning "This will deploy your backend to production."
    read -p "Continue with deployment? (y/n): " confirm

    if [ "$confirm" != "y" ]; then
        print_info "Deployment cancelled"
        exit 0
    fi

    echo ""
    print_info "Starting deployment process..."
    echo ""

    upload_env_vars
    deploy_to_railway
    wait_for_deployment

    echo ""
    print_info "Running post-deployment tasks..."
    echo ""

    run_migrations
    get_deployment_url
    verify_deployment

    echo ""
    print_header "DEPLOYMENT COMPLETE"
    echo ""
    print_success "Your backend is now live on Railway!"
    echo ""
    echo "Next steps:"
    echo "  1. Update frontend environment variables in Vercel"
    echo "  2. Test API endpoints: /health, /docs, /health/ready"
    echo "  3. Monitor logs: railway logs"
    echo "  4. Set up custom domain (optional)"
    echo ""
    print_info "View your deployment: https://railway.app/dashboard"
    echo ""
}

# Run main function
main "$@"
