#!/bin/bash

set -euxo pipefail

REMOTE_PATH="/var/www/api.ugc.bruhie.re/"
OUT="."
CONNECTION="root@$SERVER_IP"


echo -e "Removing remote folder ..."
# REMOVE_CMD="mkdir -p ${REMOTE_PATH} && cd ${REMOTE_PATH} && rm -rf *"
REMOVE_CMD="mkdir -p $REMOTE_PATH && cd $REMOTE_PATH && rm -rf *"
ssh -o strictHostKeyChecking=no -o PubkeyAuthentication=yes "$CONNECTION" "$REMOVE_CMD"

echo -e "Synchronizing files ..."
scp -o stricthostkeychecking=no -o PubkeyAuthentication=yes -r "$OUT/*" "$CONNECTION:$REMOTE_PATH"

RUN_CMD="cd $REMOTE_PATH && docker build -t ugc-back . && docker kill ugc-api || true && docker run -d -p 5000:5000 --name ugc-api --network host ugc-back"
echo -e "Deployed, building and starting"
ssh -o strictHostKeyChecking=no -o PubkeyAuthentication=yes "$CONNECTION" "$RUN_CMD"

echo -e "Started"

