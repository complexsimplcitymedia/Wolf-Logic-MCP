#!/bin/bash
# ===========================================
# COMPLEX Logic - Complete Stack Startup Script
# ===========================================
# Spins up the entire WOLF memory system:
# - Docker Swarm stack (Qdrant, PostgreSQL, Neo4j, OpenMemory API/UI)
# - MariaDB (standalone)
# - Complex Logic Dashboard
# - Wolf Backend API
#
# Usage: ./start-wolf.sh [options]
#   --no-swarm    Skip Docker Swarm deployment
#   --no-mariadb  Skip MariaDB startup
#   --no-dashboard Skip Wolf Dashboard startup
#   --stop        Stop all services
#   --status      Show status of all services

set -e

# ===========================================
# Configuration
# ===========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WOLF_LOGIC_DIR="/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-app"
COMPOSE_FILE="${WOLF_LOGIC_DIR}/docker-compose.yml"
STACK_NAME="wolf-logic"

# Service ports
WOLF_BACKEND_PORT=2501
WOLF_FRONTEND_PORT=3335
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=8687

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===========================================
# Helper Functions
# ===========================================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "\n${CYAN}=== $1 ===${NC}\n"; }

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$name is ready"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    log_warn "$name did not respond in time"
    return 1
}

# ===========================================
# Stop Services
# ===========================================
stop_services() {
    log_header "Stopping COMPLEX Logic Services"

    cd "$WOLF_LOGIC_DIR"
    log_info "Stopping Docker Compose stack"
    docker compose down 2>/dev/null || true

    log_success "All services stopped"
}

# ===========================================
# Show Status
# ===========================================
show_status() {
    log_header "COMPLEX Logic Service Status"

    echo -e "${CYAN}Docker Compose Services:${NC}"
    cd "$WOLF_LOGIC_DIR"
    docker compose ps

    echo -e "\n${CYAN}Service Health:${NC}"

    # Check each service
    if curl -s "http://localhost:$WOLF_BACKEND_PORT/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Wolf Backend (port $WOLF_BACKEND_PORT)"
    else
        echo -e "  ${RED}○${NC} Wolf Backend (port $WOLF_BACKEND_PORT)"
    fi

    if curl -s "http://localhost:$WOLF_FRONTEND_PORT" > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Wolf Frontend (port $WOLF_FRONTEND_PORT)"
    else
        echo -e "  ${RED}○${NC} Wolf Frontend (port $WOLF_FRONTEND_PORT)"
    fi

    if curl -s "http://localhost:$NEO4J_HTTP_PORT" > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Neo4j (port $NEO4J_HTTP_PORT)"
    else
        echo -e "  ${RED}○${NC} Neo4j (port $NEO4J_HTTP_PORT)"
    fi
}

# ===========================================
# Start Complex Logic Stack
# ===========================================
start_stack() {
    log_header "Starting Complex Logic Docker Compose Stack"

    cd "$WOLF_LOGIC_DIR"

    log_info "Starting services from: $COMPOSE_FILE"
    docker compose up -d --build

    log_info "Waiting for services to become healthy"
    sleep 5

    wait_for_service "http://localhost:$WOLF_BACKEND_PORT" "Wolf Backend" 30
    wait_for_service "http://localhost:$WOLF_FRONTEND_PORT" "Wolf Frontend" 30
    wait_for_service "http://localhost:$NEO4J_HTTP_PORT" "Neo4j" 60
}

# ===========================================
# Main
# ===========================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --stop)
                stop_services
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--stop|--status]"
                exit 1
                ;;
        esac
    done

    echo -e "${CYAN}"
    echo "    ██╗    ██╗ ██████╗ ██╗     ███████╗"
    echo "    ██║    ██║██╔═══██╗██║     ██╔════╝"
    echo "    ██║ █╗ ██║██║   ██║██║     █████╗  "
    echo "    ██║███╗██║██║   ██║██║     ██╔══╝  "
    echo "    ╚███╔███╔╝╚██████╔╝███████╗██║     "
    echo "     ╚══╝╚══╝  ╚═════╝ ╚══════╝╚═╝     "
    echo -e "${NC}"
    echo "    Complex Logic Application Startup"
    echo ""

    # Check prerequisites
    log_header "Checking Prerequisites"
    check_command docker || exit 1
    check_command curl || exit 1
    log_success "All prerequisites met"

    # Start services
    start_stack

    # Final status
    log_header "Startup Complete"
    show_status

    echo ""
    echo -e "${GREEN}COMPLEX Logic Application is running!${NC}"
    echo ""
    echo "Access points:"
    echo "  Wolf Frontend:    http://localhost:$WOLF_FRONTEND_PORT"
    echo "  Wolf Backend API: http://localhost:$WOLF_BACKEND_PORT"
    echo "  Neo4j Browser:    http://localhost:$NEO4J_HTTP_PORT"
    echo "  Neo4j Bolt:       bolt://localhost:$NEO4J_BOLT_PORT"
    echo ""
}

main "$@"
