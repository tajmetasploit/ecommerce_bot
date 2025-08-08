#!/bin/bash

echo "Stashing any uncommitted changes..."
git stash -u

echo "Fetching latest changes from origin..."
git fetch origin

echo "Rebasing on origin/main..."
git rebase origin/main

echo "Applying stashed changes back..."
git stash pop

echo "Adding all changes..."
git add .

echo "Committing changes..."
git commit -m "Auto commit: update from Replit" || echo "No changes to commit"

echo "Pushing to origin/main..."
git push origin main
