#!/bin/sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print success message
print_success() {
    echo "${GREEN}${BOLD}✓ $1${NC}"
}

# Function to print info message
print_info() {
    echo "${BLUE}${BOLD}→ $1${NC}"
}

# CLI configuration switcher
# Cycles through cli-local.yml -> cli-xp130.yml -> cli-xp230.yml -> cli-local.yml

echo "${BOLD}${BLUE}"
echo " ██████╗██╗     ██╗    ███████╗██╗    ██╗██╗████████╗ ██████╗██╗  ██╗"
echo "██╔════╝██║     ██║    ██╔════╝██║    ██║██║╚══██╔══╝██╔════╝██║  ██║"
echo "██║     ██║     ██║    ███████╗██║ █╗ ██║██║   ██║   ██║     ███████║"
echo "██║     ██║     ██║    ╚════██║██║███╗██║██║   ██║   ██║     ██╔══██║"
echo "╚██████╗███████╗██║    ███████║╚███╔███╔╝██║   ██║   ╚██████╗██║  ██║"
echo " ╚═════╝╚══════╝╚═╝    ╚══════╝ ╚══╝╚══╝ ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝"
echo "${NC}"
echo "${BOLD}CLI Configuration Switcher${NC}"
echo ""

# Define the configuration files in order
configs="cli-local.yml cli-xp130.yml cli-xp230.yml"

# Check current configuration
current=""
if [ -L "cli.yml" ]; then
    current=$(readlink cli.yml)
    print_info "Current configuration: ${current}"
else
    print_info "No current configuration found"
fi

# Find current config and determine next configuration
next_config=""
found=0

for config in $configs; do
    if [ "$found" = "1" ]; then
        next_config="$config"
        break
    fi
    if [ "$config" = "$current" ]; then
        found=1
    fi
done

# If no next config found (current is last or not found), start with first config
if [ -z "$next_config" ]; then
    next_config="cli-local.yml"
fi

print_info "Switching to: ${next_config}"

# Remove existing cli.yml and create new symlink
rm -f cli.yml
ln -s "$next_config" cli.yml

print_success "Successfully switched CLI configuration to: ${next_config}"

echo ""
echo "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo "${GREEN}Configuration switch completed!${NC}"
echo ""