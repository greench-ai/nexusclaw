#!/bin/bash
# NexusClaw Install Script — Freedom-first AI framework

echo "Installing NexusClaw..."

mkdir -p ~/.nexusclaw
cp -r src ~/.nexusclaw/
chmod +x ~/.nexusclaw/src/cli/main.py

# Create symlink
ln -sf ~/.nexusclaw/src/cli/main.py ~/bin/nexusclaw 2>/dev/null || \
ln -sf ~/.nexusclaw/src/cli/main.py /usr/local/bin/nexusclaw 2>/dev/null || \
echo "Add to PATH: export PATH=~/.nexusclaw/src/cli:\$PATH"

echo "Done! Run: nexusclaw setup"
