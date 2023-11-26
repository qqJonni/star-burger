#!/bin/bash
# start with the parameter ROLLBAR_ACCESS_TOKEN
echo "Start, deploy Star Burger!"
deploy_complete=true

set -e

git pull
source venv/bin/activate
python manage.py migrate
npm ci
./node_modules/.bin/parcel bundles-src/index.js --dist-dir bundles --public-url="./"
pip install -r requirements.txt
python manage.py collectstatic --noinput
deactivate

sudo systemctl restart star-burger
sudo systemctl reload nginx


last_commit=$(git rev-parse HEAD);


echo "Deploy completed successfully"
echo "Last commit {$last_commit}"
curl -H "X-Rollbar-Access-Token: $1" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "Star_burger", "revision": "{$last_commit}", "rollbar_name": "qqjonni911", "local_username": "circle-ci", "comment": "star burger deployment", "status": "succeeded"}'
