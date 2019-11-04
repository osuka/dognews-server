# Isolated Visual Studio container environment to work with this project

> I like to use Visual Studio Remote containers to hold projects and dependencies
> This documents details how that works
>
> This environment has: NodeJS and Python 3.x in the same container as I find myself using both often

Reference: [Developing inside a Container](https://code.visualstudio.com/docs/remote/containers).

This can be used to

* Isolate all the dependencies and environment visual studio code runs in
* Safeguard your local machine
* Edit from a client machine against a remote server with docker

It supports node and python as those are the likely languages I'll use here.

There's 2 or 3 files involved depending on whether we are launching the container locally or on a remote machine:

1. [.devcontainer/Dockerfile](./.devcontainer/Dockerfile) - defines a base image in which the tools will be run (eg eslint, virtualenv, nvm)
     This is shared by everybody, it doesn't have any local specific/dev specific information
     Visual Studio Code's extension Remote-Containers will launch a container using this

2. [.devcontainer/devcontainer.json](./.devcontainer/devcontainer.json) - defines the vscode environment that will run in the container
     This defines all extensions (which will typically be shared), but also has information
     particular to a user, like folder mappings. Create it from the base configuration.
     It can install additional packages in the image (versions of node etc)
     See [this microsoft example](https://aka.ms/vscode-remote/devcontainer.json) for details

3. Optional step: you can create a `myproject.code-worspace` file local to the project - to define more settings or how to get to docker (eg tunnel)
     This environment can be run in localhost or in a remote machine - what determines how it runs is
     the docker client's default. We can use a workspace file to define a docker.host setting to
     point to a remote machine. Alternatively simply do `DOCKER_HOST=xxxxx code`. See below.

## Step by step instructions

* Install Visual Studio Code on the client machine
* Install docker on the client machine
* Install the Remote Development (by Microsoft) extension on the client machine
* (optional) Install the Docker extension on the client machine (makes it easier to set DOCKER_HOST)
* git checkout this repository on the client machine

> If we want to run everything on another server (eg to have a kind of 'thin client' development machine), we need to create a tunnel to the docker socket so it can be reached (`ssh -NL localhost:23750:/var/run/docker.sock osuka@192.168.1.149`) and now we can create a new workspace and then change the workspace settings to point docker to the tunnel by changing in Visual Studio the setting:`{ "settings": { "docker.host": "127.0.0.1:23750" } }`

* Click _Open Folder_ and go to the folder of the project
* Press ctrl-alt-p and select _Remote-Containers: Reopen folder in container_ and it will check the remote host and if it doesn't find a container already it will create a new one, install all dependencies there, and restart Visual Studio Code now running mostly on the server (eg extensions run there)

You can install more extensions manually using Visual Studio, and open the terminal and install more packages etc, but all of that is running in the container and will exists only as long as the container exists. The container is started/stopped (but not deleted) whene start/exiting VSC so the changes are semi-permanent, but it's a good practice to not rely on things installed that are not in the Dockerfile or `devcontainer.json` file.

If you need special tools they can be added with apt-get commands either in the Dockerfile or in the postCreate setting in devcontainer.json. Modifying the Dockerfile means it will be recreated. Modifying devcontainer.json does not have any effect unless you recreate the environment.

Once VSC has restarted your file system is now inside the docker container, and everything is mounted in `/workspace`.
