#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The purpose of this script is to:
#  - take a URL to a Solace VMR docker container
#  - validate the container against known MD5
#  - load the container to create a local instance
#  - upload the instance into google container registery
#  - clean up load docker


OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
solace_password=""
solace_image=""
verbose=0

while getopts "i:p:z:" opt; do
    case "$opt" in
    i)  solace_image=$OPTARG
        ;;
    p)  solace_password=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))
[ "$1" = "--" ] && shift

verbose=1
echo "`date` INFO: solace_image=$solace_image ,Leftovers: $@"


echo "`date` INFO: DOWNLOAD KOMPOSE"
echo "#############################################################"
curl -L https://github.com/kubernetes/kompose/releases/download/v1.3.0/kompose-linux-amd64 -o kompose
chmod 755 kompose

cat > ./solace-compose.yaml << EOL
version: "3"
services:
  solace:
    image: ${solace_image}
    environment:
      - service_ssh_port=2222
      - username_admin_globalaccesslevel=admin
      - username_admin_password=${solace_password}
    network_mode: "host"
    userns_mode: "host"
    volumes:
      - dshm:/dev/shm
    cap_add:
      - IPC_LOCK
      - SYS_NICE
    ulimits:
      core: -1
      memlock: -1
      nofile:
        soft: 2448
        hard: 38048
    restart: always
    ports:
      - "80"
      - "8080"
      - "2222"
      - "55555"
      - "1883"
    labels:
      kompose.service.type: LoadBalancer
volumes:
  dshm:
    driver_opts:
      size: 2G
      type: tmpfs
      device: tmpfs
EOL


echo "`date` INFO: DEPLOY VMR TO CLUSTER"
echo "#############################################################"
./kompose -f ./solace-compose.yaml up

echo "`date` INFO: DEPLOY VMR COMPLETE"
echo "#############################################################"
echo "`date` INFO: View status with 'kubectl get deployment,svc,pods,pvc'"
