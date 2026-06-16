#!/bin/bash
# ============================================================
# HBM System - Public Release Builder
# ============================================================
# This script creates a clean public release by:
# 1. Excluding private files/folders
# 2. Copying only public-ready content to public/ directory
# 3. Generating a sanitized git repository
#
# Usage:
#   ./scripts/create_public_release.sh [--dry-run] [--push]
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
DRY_RUN=false
PUSH=false
PUBLIC_DIR="public_release"
PRIVATE_REMOTE="git@github.com:dysonaicom-svg/hbm-system-model-private.git"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--push]"
            echo "  --dry-run  Show what would be copied without copying"
            echo "  --push     Push public repo to remote"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} HBM System - Public Release Builder${NC}"
echo -e "${BLUE}========================================${NC}"

# ============================================================
# Step 1: Define what to EXCLUDE from public release
# ============================================================
EXCLUDE_PATTERNS=(
    # Claude AI development folder
    ".claude/"

    # MCP configuration (contains local paths)
    ".mcp.json"
    ".mcp/"

    # Development notes (may contain internal info)
    "research/hbm4-logic-base-die/notes/"
    "research/hbm4-logic-base-die/.cache/"
    "research/hbm4-logic-base-die/implementation/plan.md"

    # Experimental/unstable code
    "research/experimental/"

    # Build artifacts
    "build/"
    "dist/"
    "*.egg-info/"

    # IDE and editor files
    ".vscode/"
    ".idea/"
    "*.swp"
    "*.swo"

    # OS files
    ".DS_Store"
    "Thumbs.db"

    # Simulation outputs (large binary files)
    "*.vcd"
    "*.fsdb"
    "*.wlf"
    "sim/results/"

    # Logs
    "*.log"

    # Temporary files
    "tmp/"
    "temp/"
    "*.tmp"

    # Hidden files at root (except .gitignore, README, LICENSE)
    ".[!g]*"  # All hidden files starting with anything except 'g'
)

# ============================================================
# Step 2: Define what to ALWAYS INCLUDE
# ============================================================
ALWAYS_INCLUDE=(
    ".gitignore"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
)

# ============================================================
# Step 3: Create public directory structure
# ============================================================
echo -e "\n${YELLOW}Step 1:${NC} Setting up public directory..."

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would create:${NC} $PUBLIC_DIR/"
    echo -e "${YELLOW}[DRY RUN] Would exclude:${NC}"
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        echo "  - $pattern"
    done
    exit 0
fi

# Clean previous public directory
rm -rf "$PUBLIC_DIR"
mkdir -p "$PUBLIC_DIR"

# ============================================================
# Step 4: Copy public-ready directories
# ============================================================
echo -e "\n${YELLOW}Step 2:${NC} Copying public-ready directories..."

PUBLIC_DIRS=(
    "model"
    "sim"
    "tests"
    "examples"
    "rtl"
    "verification"
    "config"
    "scripts"
    "docs"
)

for dir in "${PUBLIC_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  Copying ${GREEN}$dir/${NC}..."
        cp -r "$dir" "$PUBLIC_DIR/"
    else
        echo -e "  Skipping ${YELLOW}$dir/${NC} (not found)"
    fi
done

# ============================================================
# Step 5: Copy essential root files
# ============================================================
echo -e "\n${YELLOW}Step 3:${NC} Copying essential files..."

for file in "${ALWAYS_INCLUDE[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  Copying ${GREEN}$file${NC}..."
        cp "$file" "$PUBLIC_DIR/"
    fi
done

# Always include these files
for file in "requirements.txt" "setup.py" "pyproject.toml" "MANIFEST.in"; do
    if [ -f "$file" ]; then
        cp "$file" "$PUBLIC_DIR/"
    fi
done

# ============================================================
# Step 6: Clean up in public directory
# ============================================================
echo -e "\n${YELLOW}Step 4:${NC} Cleaning public directory..."

cd "$PUBLIC_DIR"

# Remove any hidden files that slipped through
find . -name ".*" -type f ! -name ".gitignore" ! -name "LICENSE" -delete 2>/dev/null || true

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove .claude if somehow copied
find . -type d -name ".claude" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mcp" -exec rm -rf {} + 2>/dev/null || true

# Remove notes directories
find . -type d -name "notes" -exec rm -rf {} + 2>/dev/null || true

cd ..

# ============================================================
# Step 7: Create clean git repository
# ============================================================
echo -e "\n${YELLOW}Step 5:${NC} Creating clean git repository..."

cd "$PUBLIC_DIR"
git init
git add .
git commit -m "Initial public release

- Clean public codebase
- Excludes .claude, notes, and development files
- Ready for open source distribution

Generated by create_public_release.sh"

cd ..

# ============================================================
# Step 8: Summary
# ============================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN} Public release created successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nPublic files location: ${BLUE}$PUBLIC_DIR/${NC}"
echo -e "Total files: $(find $PUBLIC_DIR -type f | wc -l)"
echo -e "Total lines: $(find $PUBLIC_DIR -name "*.py" -o -name "*.sv" | xargs wc -l 2>/dev/null | tail -1)"

if [ "$PUSH" = true ]; then
    echo -e "\n${YELLOW}Pushing to remote...${NC}"
    cd "$PUBLIC_DIR"
    git remote add origin "$PRIVATE_REMOTE" 2>/dev/null || true
    read -p "Enter remote URL for public repo (or press Enter to skip): " remote_url
    if [ -n "$remote_url" ]; then
        git remote set-url origin "$remote_url"
        git push -u origin master
    fi
    cd ..
fi

echo -e "\n${GREEN}Done!${NC}"
echo -e "\nNext steps:"
echo -e "  1. Review ${BLUE}$PUBLIC_DIR/${NC}"
echo -e "  2. Push to your public repository"
echo -e "  3. Tag release: cd $PUBLIC_DIR && git tag v1.0.0 && git push --tags"