#!/bin/bash
# Release script for Ultimate GAU

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN} Ultimate GAU Release Script${NC}"

# Check version
VERSION=$(python -c "from ultimate_gau import __version__; print(__version__)")
echo -e "${YELLOW}Current version: $VERSION${NC}"

# Ask for version bump type
echo "Select version bump:"
echo "1) Patch (3.0.0 -> 3.0.1)"
echo "2) Minor (3.0.0 -> 3.1.0)"
echo "3) Major (3.0.0 -> 4.0.0)"
read -p "Choice [1-3]: " choice

case $choice in
    1) PART="patch";;
    2) PART="minor";;
    3) PART="major";;
    *) echo "Invalid choice"; exit 1;;
esac

# Bump version
python -c "
from version import bump_version
new_version = bump_version('$PART')
with open('ultimate_gau/__init__.py', 'r') as f:
    content = f.read()
with open('ultimate_gau/__init__.py', 'w') as f:
    f.write(content.replace('__version__ = \"$VERSION\"', f'__version__ = \"{new_version}\"'))
print(f'Version bumped to {new_version}')
"

NEW_VERSION=$(python -c "from ultimate_gau import __version__; print(__version__)")

# Commit and tag
git add ultimate_gau/__init__.py
git commit -m "Bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"

# Push
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push origin main
git push origin "v$NEW_VERSION"

echo -e "${GREEN} Release v$NEW_VERSION created!${NC}"
echo -e "${YELLOW}GitHub Actions will now publish to PyPI${NC}"
