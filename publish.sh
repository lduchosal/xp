#!/bin/sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

STEPS=15
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
echo "${BOLD}Starting XP Package Publishing Process...${NC}"

print_step "Cleaning Previous Build"
run_command "pdm run clean" "Clean"

print_step "Installing Dependencies"
run_command "pdm run install" "Dependencies installation"

print_step "Installing Development Dependencies"
run_command "pdm run install-dev" "Development dependencies installation"

print_step "Type Checking"
run_command "pdm run typecheck" "Type checking"

print_step "Code Quality Check (Refurb)"
run_command "pdm run refurb" "Code quality check"

print_step "Linting"
run_command "pdm run lint" "Linting"

print_step "Code Formatting"
run_command "pdm run format" "Code formatting"

print_step "Code dead variable check"
run_command "pdm run vulture" "Dead variable checl"

print_step "Running Tests"
run_command "pdm run test-quick" "Tests"

print_step "Bumping Version"
run_command "pdm run bump-version" "Version bump"

# Extract version after bump
VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); import xp; print(xp.__version__)")
echo "${BLUE}New version: ${VERSION}${NC}"

print_step "Building Package"
run_command "pdm build" "Package build"

print_step "Publishing Package"
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
