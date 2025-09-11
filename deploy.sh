#!/bin/bash

# Deployment script for Signaling Space Experiment
# Make sure to update the variables below before running

APP_NAME="sigspace-experiment"  # Change this to your desired app name
BUCKET_NAME="sigspace-bucket"  # Your S3 bucket name

echo "🚀 Starting deployment of Signaling Space Experiment..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged into Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Not logged into Heroku. Please run: heroku login"
    exit 1
fi

echo "✅ Heroku CLI is installed and you're logged in"

# Create Heroku app if it doesn't exist
if ! heroku apps:info $APP_NAME &> /dev/null; then
    echo "📱 Creating Heroku app: $APP_NAME"
    heroku create $APP_NAME
else
    echo "✅ Heroku app $APP_NAME already exists"
fi

# Set environment variables
echo "🔧 Setting environment variables..."
heroku config:set AWS_DEFAULT_REGION=us-east-1 --app $APP_NAME

# Add required Heroku addons
echo "📦 Adding required addons..."
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
heroku addons:create heroku-redis:mini --app $APP_NAME

echo "🎯 Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Set your AWS credentials:"
echo "   heroku config:set AWS_ACCESS_KEY_ID=your_key --app $APP_NAME"
echo "   heroku config:set AWS_SECRET_ACCESS_KEY=your_secret --app $APP_NAME"
echo ""
echo "2. Set your Prolific API token:"
echo "   heroku config:set PROLIFIC_API_TOKEN=your_token --app $APP_NAME"
echo ""
echo "3. Update the S3 bucket name in experiment.py to: $BUCKET_NAME"
echo ""
echo "4. Test deployment:"
echo "   psynet debug heroku --app $APP_NAME"
echo ""
echo "5. Deploy live:"
echo "   psynet deploy heroku --app $APP_NAME"
