FROM python:3.7-slim
LABEL maintainer="noone@localhost"

# This image installs nvm, venv and python3

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# This container intentionally runs with a non privileged user
# without sudo or password
ENV THEUSER=user
RUN useradd -m -s /bin/bash ${THEUSER}

# Install here any tool we may need to run, from extensions or from the terminal etc
# This allows us to isolate the running environment

# add deps here if needed - I've added some I find useful (awscli/jq/vim) and python3/venv
RUN apt-get update && apt-get upgrade -y && apt-get install -y apt-transport-https && \
  apt-get install -y git vim less awscli jq curl && \
  apt-get install -y python3 python3-boto python3-boto3 python3-pip virtualenv && \
  apt-get install -y sqlite3 && \
  apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# a reminder...
RUN echo "echo 'This container does not have root access at all. Connect externally via docker exec.'" >/usr/local/bin/sudo
RUN chmod guo+x /usr/local/bin/sudo

# add nvm for node js
ENV NVM_DIR="/home/${THEUSER}/.nvm"
RUN mkdir "${NVM_DIR}" && \
  echo '. $NVM_DIR/nvm.sh' >>/home/user/.bashrc && \
  echo '. $NVM_DIR/bash_completion' >>/home/user/.bashrc && \
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash
RUN chown -R ${THEUSER} "${NVM_DIR}"

# for python dependencies (normal ones can be installed from requirements.txt manually)
RUN pip install pylint

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# we don't want full root access inside the docker container but pip will want to write in /usr/local
RUN chown -R ${THEUSER} /usr/local

# everything else is done using this user
USER ${THEUSER}
