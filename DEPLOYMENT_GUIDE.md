# Deployment Guide

written using a combination of 
- cursor
- https://devcenter.heroku.com/articles/git

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

problems with versions (conflicting computer and PsyNet dallinger) and existing todos so running the following
```bash
export SKIP_VERSION_CHECK=1
export SKIP_TODO_CHECK=1
```

https://dlgr-sig-space-9e9bd574c232.herokuapp.com/ad?generate_tokens=1
https://dlgr-sig-space-365837951396.herokuapp.com/ad?generate_tokens=1


only match in study ID

###
debug deployment (test first)
```bash
psynet debug heroku --app sig-space
````

ran into issues with "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb1 in position 81: invalid start byte"
to fix this, trying:
```bash
rm -f ./snapshots/sigspace-experimen-code.zip ./snapshots/sigspace-experiment-code.zip ./source_code.zip
rm -rf ./__pycache__
```

to try to solve this, temporarily move potentially problematic files into another directory (temp_backup)
```bash
mkdir -p temp_backup
mv static/vocabtest temp_backup/
mv static/libraries temp_backup/
mv static/vis@* temp_backup/ 2>/dev/null || true
mv static/images temp_backup/
mv static/audio temp_backup/
mv static/figs temp_backup/
mv static/repp temp_backup/
mv static/generated_sounds temp_backup/
mv static/logo.png static/favicon.png static/logo_image_only.png temp_backup/
rm -rf __pycache__ && rm -f deploy.sh
```

database template needed
and make sure it is added (I think was blocked in the ignore file bc of .zip)
idk trying lots of things (incl. manually pushing to git which apparently should be handled by dallinger?? so idk)
```bash
mkdir -p .deploy && echo '{"version": "1.0", "data": {}}' > .deploy/database_template.zip
git add .deploy/ && git status --porcelain | grep deploy
git add -f .deploy/database_template.zip && git commit -m "add database template file" &
& git push heroku main

```

instead of just ```deploy heroku --app sig-space``` I need to add ```./psynet-env/bin/psynet``` in front 
to specify my venv (i/o the system-wide PsyNet installation)
```bash
./psynet-env/bin/psynet deploy heroku --app sig-space
```

live deployment
```bash
psynet deploy heroku --app your-app-name
```


if need to debug/deploy (again), first need to destroy app with same name
```bash
heroku apps:destroy dlgr-sig-space --confirm dlgr-sig-space
```

once destroyed, can run
```bash
SKIP_TODO_CHECK=1 SKIP_CHECK_PSYNET_VERSION_REQUIREMENT=1 SKIP_VERSION_CHECK=1 ./psynet-env/bin/psynet deploy heroku --app sig-space
```

build was failing because it didn't have a database file; initialize the db
```bash
heroku run "python -c 'from dallinger.db import init_db; init_db()'" --app dlgr-sig-space

```

eventually need to add back all those image files etc.

## Step 5: Prolific Setup

1. Create a study on Prolific Academic
2. Set the external study URL to your Heroku app URL
3. Configure completion redirect URL
4. Set up participant screening criteria

## Notes

- Export data when experiment is complete
- Remember to tear down Heroku resources to avoid charges




For testing locally
recruiter = cli
# asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")  # Comment out S3 for local development

