#!/bin/bash
# Git pull all repos in WolfPack
cd /mnt/WolfPack/Github
for dir in */; do
    if [ -d "$dir/.git" ]; then
        echo "Pulling $dir"
        cd "$dir"
        git pull 2>/dev/null
        cd ..
    fi
done
echo "All repos updated"
