#!/bin/bash
# Push backend to GitHub

cd /Users/robertvill/voice2task/backend

echo "🚀 Pushing backend to GitHub..."

git remote add origin https://github.com/robertvill8/orbit-backend.git
git branch -M main
git push -u origin main

echo "✅ Backend pushed to GitHub!"
echo "📍 Repository: https://github.com/robertvill8/orbit-backend"
echo ""
echo "Next: Go to Railway and select this repository for deployment"
