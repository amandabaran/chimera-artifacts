# Overview

ChimeRA is register array which utilizes the CAS-ABD protocol for replication. It is specifcally designed for implicit integer-based indexing typically seen in coordination workloads. 


## Cluster Configuration

### Cluster Prerequisites

Running all experiments requires:
* a cluster of 8 machines connected via an InfiniBand fabric,
* Ubuntu 24.04 (different systems may work, but they have not been tested),
* all machines having the following ports open: 7000-7100, 11211, 18515, 9998.

### Deployment Dependencies

#### Gateway Dependencies

The artifacts are built and packaged into binaries. Subsequently, these binaries are deployed from a *gateway* machine (e.g., your laptop).
The gateway machine requires the following depencencies installed to be able to execute the deployment (and evaluation) scripts:
```sh
sudo apt install -y coreutils gawk python3 zip tmux
```

**Optionnally**, if you want to generate the plots from the datapoints, the gateway also requires the following dependencies:
```sh
sudo apt install python3-packaging fonts-linuxlibertine
fc-cache -f -v
rm ~/.cache/matplotlib -rf
pip3 install --upgrade pip
pip3 install --upgrade importlib_resources matplotlib
```

#### Cluster Machine Dependencies

The cluster machines, assuming they are already setup for InfiniBand+RDMA, require the following dependencies to be able to execute the binaries:
```sh
sudo apt install -y coreutils gawk python3 zip tmux gcc numactl libmemcached-dev memcached openjdk-8-jre-headless
```

The proper version of Mellanox OFED's InfiniBand drivers can be installed on the cluster machines via:
```sh
wget http://www.mellanox.com/downloads/ofed/MLNX_OFED-5.3-1.0.0.1/MLNX_OFED_LINUX-5.3-1.0.0.1-ubuntu20.04-x86_64.tgz
tar xf MLNX_OFED_LINUX-5.3-1.0.0.1-ubuntu20.04-x86_64.tgz
sudo ./mlnxofedinstall
```

### Build Dependencies

To build the evaluation binaries, you need the dependencies below.
> *Note*: You can build and package the binaries in a cluster machine, the gateway or another machine. It is important, however, that you build the binaries in a machine with the same distro/version as the cluster machines, otherwise the binaries may not work. For example, you can use a docker container to build and package the binaries. Alternatively, you can use one of the machines in the cluster.

Install the required dependencies on a vanilla Ubuntu 20.04 installation via:
```sh
sudo apt update
sudo apt -y install \
    python3 python3-pip \
    gawk build-essential cmake ninja-build \
    git libssl-dev \
    libmemcached-dev \
    libibverbs-dev # only if Mellanox OFED is not installed.
pip3 install --upgrade "conan>=1.63.0,<2.0.0"
```

## Building and Deploying the Binaries

Assuming all the machines in your cluster have the same configuration, you need to:
* build all the necessary binaries, for example in a deployment machine,
* package them and deploy them on all 8 machines.

### Recursively Cloning this Repository

First, clone this repository on the gateway, including the chimera submodule, via:
```sh
git clone url --recurse-submodules
cd chimera-artifacts
```

Make sure your working path has no spaces or special characters (e.g. `/home/user/chimera-artifacts` is fine).

### Building the Binaries

Build the evaluation binaries via:
```sh
./bin/chimera/build.sh distclean buildclean clean # cleans potential leftovers
./bin/chimera/build.sh chimera swarm-kv fusee
./bin/chimera/build.sh chimera swarm-kv fusee # due to conan concurrency issues, the first command might run into missing dependencies 
```

Binaries for ChimeRA, SWARM-KV and FUSEE will appear in `bin/chimera/chimera/build/bin`, `bin/chimera/swarm-kv/build/bin` and `bin/chimera/fusee/build/bin`, respectively.

### Downloading YCSB

Download YCSB binaries via:
```sh
./download-ycsb.sh
```

This should download `ycsb-0.12.0.tar.gz` in the current directory, and print `ycsb-0.12.0.tar.gz: OK` if the checksum matches.

### Deploying the Binaries

Zip the binaries and prepare their deployment via:
```sh
./bin/zip-binaries.sh
./prepare-deployment.sh # generates deployment.zip
```

Then, for each cluster server, you will need to:
- create a `chimera-artifacts` directory with the same path as the one on the gateway,
- send `deployment.zip` to said directory,
- unzip `deployment.zip` in said directory,
- untar `chimera-artifacts/ycsb-0.12.0.tar.gz` in said directory,
- rename the `chimera-artifacts/ycsb-0.12.0` directory to `chimera-artifacts/YCSB`,
- unzip `chimera-artifacts/bin/bin.zip` in the `chimera-artifacts/bin` directory.

This can also be done from the gateway via a single:
```sh
./send-deployment.sh
```

If anything goes wrong, or you want to clean workers, you can undo the deployment via `./undo-deployment.sh`. This will also delete remote logs.

Once the deployment is done, do not move the `chimera-artifacts` directory.

As a sanity check, the `chimera-artifacts` directory of each worker should contain the `bin`, `experiments`, `scripts`, `workloads` and `YCSB` subdirectories.

## Running Experiments

### Experiments

Once the binaries are deployed, you can reproduce the results presented in our paper from the gateway by running the following scripts.
During the kick-the-tires period, we invite you to run the scripts of [figure 5](#figure-5) as a sanity check.

> Note: Due to differences in hardware and software configuration, you can expect the pre-configured cluster we provide to achieve up to both 10% higher latency and 10% lower throughput than the setup used in the accepted version of the paper.
> However, such degradations should not affect the behaviors and relative comparisons presented in the paper.

Each experiment takes roughly takes ~15-30 minutes to run.

# Troubleshooting
If you see errors like:
.can't find window: server1

Run ./scripts/kill-all-tmux.sh


This repository was orignially forked from SWARM and utlizes much of its RDMA framework and documentation. 