#!/bin/bash

set -e #exit on error

#Redeploy to Cloudlab cluster machines after rebuilding

#Build
./bin/chimera/build.py distclean buildclean clean
./bin/chimera/build.py all
wait

#Zip Binaries
./bin/zip-binaries.sh
wait

#Prepare Deployment with zip
./prepare-deployment.sh
wait

#Send to cluster machines in parallel
./send-deployment.sh
