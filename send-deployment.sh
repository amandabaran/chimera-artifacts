#!/bin/bash
set -e

BASE_DIR="$( realpath -sm  "$( dirname "${BASH_SOURCE[0]}" )")"
cd "$BASE_DIR"

# Library path for GCC 13 and Conan deps
LIB_PATH="$BASE_DIR/bin/chimera/.deps/gcc/relwithdebinfo/lib"

for i in {1..8}; do
  echo "---------------------------------------"
  echo "Sending deployment to w$i"
  
  # Create directory structure
  ssh w$i "mkdir -p \"$BASE_DIR\""
  
  # Transfer the deployment package
  scp deployment.zip w$i:"$BASE_DIR/deployment.zip"
  
  # Extract, Setup, and handle the environment file
  ssh w$i "cd \"$BASE_DIR\"; \
           # 1. Clean out the old conflicting dir if it exists
           rm -rf bin/chimera; \
           unzip -o deployment.zip; \
           tar -xf ycsb-0.12.0.tar.gz; \
           rm -rf YCSB; mv ycsb-0.12.0 YCSB; \
           # 2. Extract binaries
           cd bin; unzip -o -q bin.zip; \
           # 3. Create a symlink so scripts looking for 'bin/chimera' find the binary
           ln -sf chimera-bin chimera-exe; \
           echo 'Deployment extraction complete on w$i'"
done

echo "---------------------------------------"
echo "Deployment successful to all nodes."