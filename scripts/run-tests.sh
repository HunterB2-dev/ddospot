#!/bin/bash

# DDoSPot Test Runner
# Execute test suite with various configurations

PROJECT_DIR="/home/hunter/Projekty/ddospot"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$PROJECT_DIR" || exit 1

log_info() { echo -e "${BLUE}[INFO]${NC} $@"; }
log_success() { echo -e "${GREEN}[✓]${NC} $@"; }
log_error() { echo -e "${RED}[✗]${NC} $@"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $@"; }

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     DDoSPot Test Suite Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

# Check pytest
log_info "Checking pytest..."
if python3 -m pytest --version &> /dev/null; then
    python3 -m pytest --version | sed 's/^/   /'
else
    log_warning "pytest not installed. Installing..."
    python3 -m pip install pytest pytest-cov > /dev/null 2>&1
    if python3 -m pytest --version &> /dev/null; then
        log_success "pytest installed"
    else
        log_error "Failed to install pytest"
        exit 1
    fi
fi
echo

# Menu
show_menu() {
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test Options:${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo "  1. Run all tests (verbose)"
    echo "  2. Run all tests (quiet)"
    echo "  3. Run with coverage report"
    echo "  4. Run API endpoint tests"
    echo "  5. Run security tests"
    echo "  6. Run core module tests"
    echo "  7. Run CLI tests"
    echo "  8. Run ML model tests"
    echo "  9. Run only unit tests"
    echo "  10. Run only integration tests"
    echo "  11. Run tests matching pattern"
    echo "  12. Run failed tests only"
    echo "  13. Stop on first failure"
    echo "  14. Generate HTML coverage report"
    echo "  15. Collect tests (don't run)"
    echo "  0. Exit"
    echo
}

# Run all tests verbose
run_all_verbose() {
    log_info "Running all tests (verbose)..."
    python3 -m pytest tests/ -v --tb=short
}

# Run all tests quiet
run_all_quiet() {
    log_info "Running all tests (quiet)..."
    python3 -m pytest tests/ -q
}

# Run with coverage
run_coverage() {
    log_info "Running tests with coverage report..."
    python3 -m pytest tests/ --cov=app --cov=core --cov=ml --cov=telemetry \
        --cov-report=term-missing --cov-report=term
}

# Run specific test modules
run_api_tests() {
    log_info "Running API endpoint tests..."
    python3 -m pytest tests/test_api_endpoints.py -v
}

run_security_tests() {
    log_info "Running security tests..."
    python3 -m pytest tests/test_security.py -v -m security
}

run_core_tests() {
    log_info "Running core module tests..."
    python3 -m pytest tests/test_core_modules.py -v
}

run_cli_tests() {
    log_info "Running CLI tests..."
    python3 -m pytest tests/test_cli.py -v
}

run_ml_tests() {
    log_info "Running ML model tests..."
    python3 -m pytest tests/test_ml_model.py -v
}

run_unit_tests() {
    log_info "Running unit tests only..."
    python3 -m pytest tests/ -m unit -v
}

run_integration_tests() {
    log_info "Running integration tests only..."
    python3 -m pytest tests/ -m integration -v
}

run_pattern_match() {
    read -p "Enter test pattern (e.g., 'test_get'): " pattern
    log_info "Running tests matching: $pattern"
    python3 -m pytest tests/ -k "$pattern" -v
}

run_failed_only() {
    log_info "Running failed tests from last run..."
    python3 -m pytest tests/ --lf -v
}

run_stop_first() {
    log_info "Running tests (stop on first failure)..."
    python3 -m pytest tests/ -x -v
}

generate_html_report() {
    log_info "Generating HTML coverage report..."
    python3 -m pip install pytest-html > /dev/null 2>&1
    python3 -m pytest tests/ \
        --cov=app --cov=core --cov=ml --cov=telemetry \
        --cov-report=html \
        --html=test-report.html \
        -v
    log_success "Reports generated:"
    echo "   Coverage: htmlcov/index.html"
    echo "   Tests:    test-report.html"
}

collect_tests() {
    log_info "Collecting tests without running..."
    python3 -m pytest tests/ --collect-only
}

# Main loop
while true; do
    show_menu
    read -p "Select option: " choice
    echo
    
    case $choice in
        1) run_all_verbose ;;
        2) run_all_quiet ;;
        3) run_coverage ;;
        4) run_api_tests ;;
        5) run_security_tests ;;
        6) run_core_tests ;;
        7) run_cli_tests ;;
        8) run_ml_tests ;;
        9) run_unit_tests ;;
        10) run_integration_tests ;;
        11) run_pattern_match ;;
        12) run_failed_only ;;
        13) run_stop_first ;;
        14) generate_html_report ;;
        15) collect_tests ;;
        0)
            log_success "Goodbye!"
            exit 0
            ;;
        *)
            log_error "Invalid option"
            echo
            ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done
