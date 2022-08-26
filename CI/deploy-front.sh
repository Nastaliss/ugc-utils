#!/bin/bash

set -euxo pipefail

REMOTE_PATH="/var/www/ugc.bruhie.re/"
OUT="./build"
CONNECTION="root@$SERVER_IP"

npm run build

echo -e "Removing remote folder ..."
# REMOVE_CMD="mkdir -p ${REMOTE_PATH} && cd ${REMOTE_PATH} && rm -rf *"
REMOVE_CMD="mkdir -p $REMOTE_PATH && cd $REMOTE_PATH && rm -rf *"
ssh -o strictHostKeyChecking=no -o PubkeyAuthentication=yes $CONNECTION "$REMOVE_CMD"

echo -e "Synchronizing files ..."
scp -o stricthostkeychecking=no -o PubkeyAuthentication=yes -r "$OUT/*" "$CONNECTION:$REMOTE_PATH"

echo -e "Deployed"
