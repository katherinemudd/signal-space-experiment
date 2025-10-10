# Deployment Guide

written using a combination of 
- cursor & https://devcenter.heroku.com/articles/git

## Prep

1. **AWS**: Set up an AWS account and create an S3 bucket
2. **Heroku**: Create a Heroku account
3. **Prolific**: Set up a Prolific Academic account
4. **PsyNet code on local git**: Have your PsyNet code ready and on a local git


## AWS S3 Setup

1. Create S3 bucket (here, called `sigspace-bucket`)
2. Make the bucket public for static assets
3. Create IAM user with S3 permissions
4. Bucket name configured in `experiment.py`:
   ```python
   asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")
   ```

## Environment Variables from AWS -> Heroku
Set these environment variables in Heroku (do NOT put them in file and push to git!):

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# Prolific Configuration
PROLIFIC_API_TOKEN=your_prolific_api_token
```

## Test code locally and link to Heroku
make sure the experiment is running locally
```bash
psynet debug local
```

create app in Heroku (name here = sig-space) and link git repo to app name
```bash
heroku create sig-space 
heroku git:remote -a sig-space
```

can check if it is linked
```bash
git remote -v
```
if it is linked then will show output (heroku + git link + fetch/push)


## Deploy to Heroku  https://deepwiki.com/search/how-do-i-deploy-experiments-on_cb1f9a9a-e5bb-4042-abc0-460e654ed105

```bash
psynet deploy heroku --app sig-space
```

if problems with versions (conflicting computer and PsyNet dallinger) and existing todos so running the following
```bash
export SKIP_VERSION_CHECK=1
export SKIP_TODO_CHECK=1
```

for testing, get link like https://dlgr-sig-space-9e9bd574c232.herokuapp.com/
add ad?generate_tokens=1 which yields values for participant_id, study_id and .._id
https://dlgr-sig-space-9e9bd574c232.herokuapp.com/ad?generate_tokens=1
for testing in a dyad: only match in study ID



## Step 5: Prolific Setup

1. Create a study on Prolific Academic
2. Set the external study URL to your Heroku app URL
3. Configure completion redirect URL
4. Set up participant screening criteria

## Run experiment from Prolific

When experiment is done, collect data
try:
```bash
psynet export heroku --app my-app-name
psynet export local
psynet export ssh --app my-app-name    
#psynet export heroku --app dlgr-sig-space --path ~/psynet-export
```

Then stop experiment to avoid Heroku charges


Changes for testing locally:
config.txt: recruiter = prolific => recruiter = cli
experiment.py: # asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")  # Comment out S3 for local development

exporting data locally:
```bash
cd /Users/katherinemudd/PsyNet/demos/experiments/sig_space_until_correct
psynet export local --path ~/psynet-export --no-source
```
