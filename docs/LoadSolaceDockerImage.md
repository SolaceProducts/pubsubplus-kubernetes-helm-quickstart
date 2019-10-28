### Step 3 (Optional): Load the Solace Docker image to a private Docker image registry

**Hint:** You may skip the rest of this step if not using a private Docker image registry (Harbor). The free PubSub+ Standard Edition is available from the [public Docker Hub registry](//hub.docker.com/r/solace/solace-pubsub-standard/tags/ ), the image reference is `solace/solace-pubsub-standard:<TagName>`.

To get the Solace message broker Docker image URL, go to the Solace Developer Portal and download the Solace PubSub+ software message broker as a **docker** image or obtain your version from Solace Support.

| PubSub+ Standard<br/>Docker Image | PubSub+ Enterprise Evaluation Edition<br/>Docker Image
| :---: | :---: |
| Free, up to 1k simultaneous connections,<br/>up to 10k messages per second | 90-day trial version, unlimited |
| [Download Standard docker image](http://dev.solace.com/downloads/ ) | [Download Evaluation docker image](http://dev.solace.com/downloads#eval ) |

If using Harbor for private Docker registry, use the `upload_harbor.sh` script provided in the `scripts` directory. You can pass the Solace image reference as a public Docker image location or a Http download Url (the Solace image `md5` checksum must also be available from the Http download Url). Also provide the Harbor host and project names and additionally, if using signed images set the `DOCKER_CONTENT_TRUST=1` and `DOCKER_CONTENT_TRUST_SERVER` environment variables. Check the script inline comments for defaults.

Note: Ensure the project with a user configured exists in Harbor, Docker is logged in to the Harbor server as user, as well as Docker Notary is configured for Harbor if using signed images. Consult your Harbor documentation for details. 

```sh
cd ~/workspace/solace-pks/scripts
# Define variables up-front to be passed to the "upload_harbor" script:
[SOLACE_IMAGE_URL=<docker-repo-or-download-link>] \
  HARBOR_HOST=<hostname> \
  [HARBOR_PROJECT=<project>] \
  [DOCKER_CONTENT_TRUST=[0|1] \
  [DOCKER_CONTENT_TRUST_SERVER=<full-server-url-with-port>] \
  upload_harbor.sh
## Example-1: upload the latest from Docker Hub to Harbor
HARBOR_HOST=<harbor-server> ./upload_harbor.sh
## Example-2: upload from a Http Url to Harbor
HARBOR_HOST=<harbor-server> \
SOLACE_IMAGE_URL=https://<server-location>/solace-pubsub-standard-9.1.0.118-docker.tar.gz ./upload_harbor.sh
```

To load the Solace Docker image into other private Docker registry, follow the general steps below; for specifics, consult the documentation of the registry you are using.

* Prerequisite: local installation of [Docker](//docs.docker.com/get-started/ ) is required
* First load the image to the local docker registry:
```sh
# Option a): If you have a local tar.gz Docker image file
sudo docker load -i <solace-pubsub-XYZ-docker>.tar.gz
# Option b): You can use the public Solace Docker image from Docker Hub
sudo docker pull solace/solace-pubsub-standard:latest # or specific <TagName>

# Verify the image has been loaded and note the associated "IMAGE ID"
sudo docker images
```
* Login to the private registry:
```sh
sudo docker login <private-registry> ...
```
* Tag the image with the desired name and tag:
```sh
sudo docker tag <image-id> <private-registry>/<path>/<image-name>:<tag>
```
* Push the image to the private registry
```sh
sudo docker push <private-registry>/<path>/<image-name>:<tag>
```

Note that additional steps may be required if using signed images.
