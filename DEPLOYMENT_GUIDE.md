# Deployment Guide for Signaling Space Experiment

## Prerequisites

1. **AWS Account**: Set up an AWS account and create an S3 bucket
2. **Heroku Account**: Create a Heroku account
3. **Prolific Academic Account**: Set up a Prolific Academic researcher account

## Step 1: AWS S3 Setup

1. ✅ S3 bucket created: `sigspace-bucket`
2. Make the bucket public for static assets
3. Create IAM user with S3 permissions
4. ✅ Bucket name configured in `experiment.py`:
   ```python
   asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")
   ```

## Step 2: Environment Variables

Set these environment variables in Heroku:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# Prolific Configuration
PROLIFIC_API_TOKEN=your_prolific_api_token
```

## Step 3: Update Configuration

1. Update `config.txt` with your actual email and organization
2. Update the completion code in `config.txt`
3. Adjust payment amounts as needed

## Step 4: Deploy to Heroku

```bash
# Debug deployment (test first)
psynet debug heroku --app your-app-name

# Live deployment
psynet deploy heroku --app your-app-name
```

## Step 5: Prolific Setup

1. Create a study on Prolific Academic
2. Set the external study URL to your Heroku app URL
3. Configure completion redirect URL
4. Set up participant screening criteria

## Step 6: Monitor and Manage

- Use Heroku dashboard to monitor performance
- Use PsyNet dashboard to monitor experiment progress
- Export data when experiment is complete
- Remember to tear down Heroku resources to avoid charges

## Important Notes

- Test thoroughly in debug mode before live deployment
- Monitor costs on both Heroku and AWS
- Set up proper error monitoring
- Have a backup plan for data collection
