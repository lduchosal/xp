#!/bin/sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Parse command line arguments
QUALITY_ONLY=false
for arg in "$@"; do
    case $arg in
        --quality)
            QUALITY_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--quality] [--help]"
            echo ""
            echo "Options:"
            echo "  --quality       Run only quality checks without publishing"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set total steps based on mode
if [ "$QUALITY_ONLY" = true ]; then
    STEPS=13
else
    STEPS=20
fi
STEP=0

# Function to print step headers
print_step() {
    STEP=$((STEP + 1))
    echo ""
    echo "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo "${BLUE}${BOLD}  $STEP/$STEPS $1${NC}"
    echo "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to print success message
print_success() {
    echo "${GREEN}${BOLD}✓ $1${NC}"
}

# Function to print error message and exit
print_error() {
    echo "${RED}${BOLD}✗ $1${NC}"
    exit 1
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"

    echo "${YELLOW}→ Running: ${cmd}${NC}"

    if eval "$cmd"; then
        print_success "$description completed successfully"
    else
        print_error "$description failed"
    fi
}

echo "${BOLD}${BLUE}"
echo "██████╗ ██╗   ██╗██████╗ ██╗     ██╗███████╗██╗  ██╗"
echo "██╔══██╗██║   ██║██╔══██╗██║     ██║██╔════╝██║  ██║"
echo "██████╔╝██║   ██║██████╔╝██║     ██║███████╗███████║"
echo "██╔═══╝ ██║   ██║██╔══██╗██║     ██║╚════██║██╔══██║"
echo "██║     ╚██████╔╝██████╔╝███████╗██║███████║██║  ██║"
echo "╚═╝      ╚═════╝ ╚═════╝ ╚══════╝╚═╝╚══════╝╚═╝  ╚═╝"
echo "${NC}"
if [ "$QUALITY_ONLY" = true ]; then
    echo "${BOLD}Starting XP Package Quality Checks...${NC}"
else
    echo "${BOLD}Starting XP Package Publishing Process...${NC}"
fi

print_step "Cleaning Previous Build (pdm run clean)"
run_command "pdm run clean" "Clean"

print_step "Installing Dependencies (pdm install)"
run_command "pdm run install" "Dependencies installation"

print_step "Installing Development Dependencies (pdm install-dev)"
run_command "pdm run install-dev" "Development dependencies installation"

print_step "Checking for Outdated Dependencies (pdm outdated)"
run_command "pdm outdated" "Outdated Dependencies"

print_step "Updating Dependencies (pdm update)"
run_command "pdm update" "Dependencies update"

print_step "Type Checking (typecheck)"
run_command "pdm run typecheck" "Type checking"

print_step "Code Quality Check (refurb)"
run_command "pdm run refurb" "Code quality check"

print_step "Linting (ruff)"
run_command "pdm run lint" "Linting"

print_step "Converting to Absolute Imports (absolufy-imports)"
run_command "pdm run absolufy" "Import conversion"

print_step "Sorting Imports (isort)"
run_command "pdm run isort" "Import sorting"

print_step "Code Formatting (black)"
run_command "pdm run format" "Code formatting"

print_step "Dead code check (vulture)"
run_command "pdm run vulture" "Dead code check"

print_step "Running Tests (pytest)"
run_command "pdm run test-quick" "Tests"

# Exit here if --no-publish flag is set
if [ "$QUALITY_ONLY" = true ]; then
    echo ""
    echo "${GREEN}${BOLD}🎉 QUALITY CHECKS COMPLETED SUCCESSFULLY! 🎉${NC}"
    echo "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo "${GREEN}All quality checks have passed. Your code is ready for publishing!${NC}"
    echo ""
    exit 0
fi

print_step "Bumping Version (pdm-bump)"
run_command "pdm run bump-version" "Version bump"

# Extract version after bump
VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); import xp; print(xp.__version__)")
echo "${BLUE}New version: ${VERSION}${NC}"

print_step "Updating README (pdm run update-readme)"
run_command "pdm run update-readme" "README update"

print_step "Building Package (pdm)"
run_command "pdm build" "Package build"

print_step "Publishing Package (twine)"
run_command "pdm publish" "Package publishing"

print_step "Adding All Files to Git"
run_command "git add ." "Adding all files to git"

print_step "Committing Changes"
COMMIT_MSG="chore: release version ${VERSION}"
run_command "git commit -m \"${COMMIT_MSG}\"" "Git commit"

print_step "Creating Tag and Pushing"
run_command "git tag conson-xp-${VERSION}" "Creating git tag"
run_command "git push" "Pushing commits"
run_command "git push --tags" "Pushing tags"

echo ""
echo "${GREEN}${BOLD}🎉 PUBLISHING COMPLETED SUCCESSFULLY! 🎉${NC}"
echo "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo "${GREEN}Your XP package has been successfully published and tagged!${NC}"
echo ""
