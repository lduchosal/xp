#!/bin/sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print step headers
print_step() {
    echo ""
    echo "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo "${BLUE}${BOLD}  $1${NC}"
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

print_step "1/13 Cleaning Previous Build"
run_command "pdm run clean" "Clean"

print_step "2/13 Installing Dependencies"
run_command "pdm run install" "Dependencies installation"

print_step "3/13 Installing Development Dependencies"
run_command "pdm run install-dev" "Development dependencies installation"

print_step "4/13 Type Checking"
run_command "pdm run typecheck" "Type checking"

print_step "5/13 Code Quality Check (Refurb)"
run_command "pdm run refurb" "Code quality check"

print_step "6/13 Linting"
run_command "pdm run lint" "Linting"

print_step "7/13 Running Tests"
run_command "pdm run test-quick" "Tests"

print_step "8/13 Bumping Version"
run_command "pdm run bump-version" "Version bump"

# Extract version after bump
VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); import xp; print(xp.__version__)")
echo "${BLUE}New version: ${VERSION}${NC}"

print_step "9/13 Building Package"
run_command "pdm build" "Package build"

print_step "10/13 Publishing Package"
run_command "pdm publish" "Package publishing"

print_step "11/13 Adding All Files to Git"
run_command "git add ." "Adding all files to git"

print_step "12/13 Committing Changes"
COMMIT_MSG="chore: release version ${VERSION}"
run_command "git commit -m \"${COMMIT_MSG}\"" "Git commit"

print_step "13/13 Creating Tag and Pushing"
run_command "git tag conson-xp-${VERSION}" "Creating git tag"
run_command "git push" "Pushing commits"
run_command "git push --tags" "Pushing tags"

echo ""
echo "${GREEN}${BOLD}🎉 PUBLISHING COMPLETED SUCCESSFULLY! 🎉${NC}"
echo "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo "${GREEN}Your XP package has been successfully published and tagged!${NC}"
echo ""
