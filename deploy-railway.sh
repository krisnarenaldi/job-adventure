#!/bin/bash

# Railway Deployment Script
# This script helps you deploy to Railway free plan

set -e

echo "🚀 Railway Deployment Helper"
echo "=============================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please log in to Railway:"
    railway login
fi

echo "✅ Authenticated"
echo ""

# Ask user which requirements to use
echo "📋 Which requirements file do you want to use?"
echo "1) requirements-railway.txt (Optimized for free plan, ~650MB)"
echo "2) requirements.txt (Current, with CPU-only PyTorch, ~650MB)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "📝 Using requirements-railway.txt"
    cp backend/requirements-railway.txt backend/requirements.txt
    echo "✅ Copied requirements-railway.txt to requirements.txt"
elif [ "$choice" = "2" ]; then
    echo "📝 Using existing requirements.txt"
else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""

# Check if project is linked
echo "🔗 Checking Railway project..."
if ! railway status &> /dev/null; then
    echo "No Railway project linked."
    echo ""
    echo "Do you want to:"
    echo "1) Create a new Railway project"
    echo "2) Link to an existing project"
    echo ""
    read -p "Enter choice (1 or 2): " project_choice
    
    if [ "$project_choice" = "1" ]; then
        echo "Creating new Railway project..."
        railway init
    elif [ "$project_choice" = "2" ]; then
        echo "Linking to existing project..."
        railway link
    else
        echo "❌ Invalid choice"
        exit 1
    fi
fi

echo "✅ Railway project linked"
echo ""

# Show current environment variables
echo "📊 Current environment variables:"
railway variables
echo ""

# Ask if user wants to set environment variables
read -p "Do you want to set/update environment variables? (y/n): " set_vars

if [ "$set_vars" = "y" ] || [ "$set_vars" = "Y" ]; then
    echo ""
    echo "Setting environment variables..."
    echo "You can also set these in the Railway dashboard: https://railway.app"
    echo ""
    
    read -p "DATABASE_URL (NeonDB connection string): " db_url
    if [ ! -z "$db_url" ]; then
        railway variables set DATABASE_URL="$db_url"
    fi
    
    read -p "SECRET_KEY (generate a strong random key): " secret_key
    if [ ! -z "$secret_key" ]; then
        railway variables set SECRET_KEY="$secret_key"
    fi
    
    read -p "ANTHROPIC_API_KEY (optional, press enter to skip): " anthropic_key
    if [ ! -z "$anthropic_key" ]; then
        railway variables set ANTHROPIC_API_KEY="$anthropic_key"
    fi
    
    # Set default values
    railway variables set ENVIRONMENT="production"
    railway variables set ALGORITHM="HS256"
    railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"
    
    echo "✅ Environment variables set"
fi

echo ""
echo "🚀 Ready to deploy!"
echo ""
echo "Deployment options:"
echo "1) Deploy now (railway up)"
echo "2) Just prepare (don't deploy yet)"
echo ""
read -p "Enter choice (1 or 2): " deploy_choice

if [ "$deploy_choice" = "1" ]; then
    echo ""
    echo "🚀 Deploying to Railway..."
    railway up
    
    echo ""
    echo "✅ Deployment initiated!"
    echo ""
    echo "📊 Check deployment status:"
    echo "   railway status"
    echo ""
    echo "📝 View logs:"
    echo "   railway logs"
    echo ""
    echo "🌐 Open in browser:"
    echo "   railway open"
    echo ""
    echo "⚠️  Don't forget to:"
    echo "   1. Add Redis service in Railway dashboard"
    echo "   2. Run database migrations: railway run alembic upgrade head"
    echo "   3. Update CORS_ORIGINS with your frontend URL"
    echo "   4. Deploy frontend to Vercel"
    
elif [ "$deploy_choice" = "2" ]; then
    echo ""
    echo "✅ Preparation complete!"
    echo ""
    echo "To deploy later, run:"
    echo "   railway up"
else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""
echo "📚 For more information, see RAILWAY_DEPLOYMENT.md"
echo ""

