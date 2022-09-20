FROM python:3.10-slim
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
  apt-get install -y python3 python3-boto python3-boto3 python3-pip && \
  apt-get install -y sqlite3 && \
  apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# a reminder...
RUN echo "echo 'This container does not have root access at all" >/usr/local/bin/sudo
RUN chmod guo+x /usr/local/bin/sudo

# add nvm for node js
ENV NVM_DIR="/home/${THEUSER}/.nvm"
RUN mkdir "${NVM_DIR}" && \
  echo '. $NVM_DIR/nvm.sh' >>/home/user/.bashrc && \
  echo '. $NVM_DIR/bash_completion' >>/home/user/.bashrc && \
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
RUN chown -R ${THEUSER} "${NVM_DIR}"

# copy first requirements, so we only reinstall them if changed
ADD requirements-common.txt /app/
RUN cd /app && \
    python3 -m venv /app/.venv && \
    . /app/.venv/bin/activate && \
    python3 -m pip install --upgrade pip && \
    pip3 install -r requirements-common.txt

COPY custom_admin_actions /app/custom_admin_actions
COPY dogauth /app/dogauth
COPY dognews /app/dognews
COPY public /app/public
COPY manage.py passenger_wsgi.py /app/
COPY uploaded_images /app/uploaded_images
RUN find /app -type d -not -path "./.venv/*" -exec chmod go+x "{}" \; && \
    chmod -R go+r /app/*.py /app/custom_admin_actions /app/dognews /app/dogauth /app/public && \
    chown -R ${THEUSER} /app/uploaded_images/ && \
    echo "Done"

# everything else is done using this user
USER ${THEUSER}

ENTRYPOINT [ "/app/" ]
