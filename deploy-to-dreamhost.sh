#!/bin/bash

# ============================================================
# Deploy script for Ubuntu 18.04.x LTS servers
#
# * Installs local versions of python and openssl
# * Creates a .venv
# * Installs dependecies for th environment (eg mysql)
# * Runs all django migrations
# * Creates a passenger_wsgi.py file
#
# I use it for Dreamhost for very cheap Django hosting, should
# work in any shared hosting that provides local ssh access
#
# Requirements: a domain or subdomain created in Dreamhost's
# panel with passenger support (or a similar setup)
# ============================================================

PYTHON_VERSION=3.7.3
OPENSSL_VERSION=1.1.1
ENVIRONMENT=dreamhost


function check_configuration() {
  . ./config.local.sh

  if [[ -z "${TARGET_USER}" ]] || [[ -z "${TARGET_HOST}" ]] || [[ -z "${TARGET_FOLDER}" ]] ; then
    echo "Missing target server configuration variables"
    exit 1
  fi

  if [[ -z "${SUPERUSER_NAME}" ]] || [[ -z "${SUPERUSER_EMAIL}" ]] ; then
    echo "Missing superuser configuration variables"
    exit 1
  fi
}

function install_openssl() {
  ssh ${TARGET_USER}@${TARGET_HOST} \
    wget -c -N -O \"openssl-${OPENSSL_VERSION}.tar.gz\" \"https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz\"

  ssh ${TARGET_USER}@${TARGET_HOST} \
    tar xzf \"openssl-${OPENSSL_VERSION}.tar.gz\"

  ssh ${TARGET_USER}@${TARGET_HOST} \
    "cd openssl-${OPENSSL_VERSION}; \
    ./config --prefix=${TARGET_FOLDER}/openssl --openssldir=${TARGET_FOLDER}/openssl no-ssl2; \
    make; \
    make install;"
  # echo 'export PATH=$HOME/openssl/bin:$PATH' >>~/.bash_profile
  # echo 'export LD_LIBRARY_PATH=$HOME/openssl/lib' >>~/.bash_profile
}

function install_python() {
  ssh ${TARGET_USER}@${TARGET_HOST} \
    wget -O "python-${PYTHON_VERSION}.tgz" -c -N "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"

  ssh ${TARGET_USER}@${TARGET_HOST} \
    tar xzf "python-${PYTHON_VERSION}.tgz"

  ssh ${TARGET_USER}@${TARGET_HOST} "mkdir -p ${TARGET_FOLDER}/opt"

  ssh ${TARGET_USER}@${TARGET_HOST} \
    "cd Python-${PYTHON_VERSION}; \
    export LDFLAGS=\"-L${TARGET_FOLDER}/openssl/lib -Wl,-rpath=${TARGET_FOLDER}/openssl/lib\"; \
    export LD_LIBRARY_PATH=\"${TARGET_FOLDER}/openssl/lib\"; \
    export CPPFLAGS=\"-I${TARGET_FOLDER}/openssl/include/openssl\"; \
    ./configure --prefix=${TARGET_FOLDER}/opt/python; \
    make; \
    make install"
    # note: -Wl,-rpath=xxx ==> so the openssl module path is included in the python binary
    # and doesn't need an external LD_LIBRARY_PATH

# # use our custom openssl install (inserting tabs gets complicated with an editor that removes TABS...)
# TAB="$(printf '\t')"
    # cd Modules; \
#     cat >Setup.local" <<EOL
# SSL=${TARGET_FOLDER}/openssl
# _ssl _ssl.c \\
# ${TAB}-DUSE_SSL -I\$(SSL)/include -I\$(SSL)/include/openssl \\
# ${TAB}-L\$(SSL)/lib -lssl -lcrypto
EOL


  ssh ${TARGET_USER}@${TARGET_HOST} \
    "cd Python-${PYTHON_VERSION}; \
    make; \
    make install"

  # ssh ${TARGET_USER}@${TARGET_HOST} \
  #   "cd Python-${PYTHON_VERSION}; \
  #   ./configure --prefix=${TARGET_FOLDER}/opt/python; \
  #   make; \
  #   make install"

  # echo "export PATH=$HOME/opt/python/bin:"'$PATH' >>~/.bash_profile
}

function create_passenger_configuration() {
  # See https://help.dreamhost.com/hc/en-us/articles/215769548-Passenger-and-Python-WSGI
  # Dreamhost's passenger configuration requires a custom entry point that
  # switches python interpreters

  ssh ${TARGET_USER}@${TARGET_HOST} "cat >${TARGET_FOLDER}/passenger_wsgi.py" <<EOL
import sys
import os
from django.core.wsgi import get_wsgi_application
INTERP = "${TARGET_FOLDER}/.venv/bin/python3"
# INTERP is present twice so that the new Python interpreter knows
# the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
# the rest of this file is the standard django wsgi.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dognews.settings.${ENVIRONMENT}')
application = get_wsgi_application()
EOL
}

# ------------------------------------------------------------------------
# INSTALL DEPENDENCIES (IF NEEDED), COPY NEW SOURCE, RUN DJANGO MIGRATIONS
# ------------------------------------------------------------------------

check_configuration

echo "* Update project source"
rsync --progress -r --size-only --exclude __pycache__ dognews restapi manage.py requirements-common.txt requirements-${ENVIRONMENT}.txt "${TARGET_USER}@${TARGET_HOST}:${TARGET_FOLDER}"/

echo "* Check openssl"
INSTALLED_SSL_VERSIONS=`ssh ${TARGET_USER}@${TARGET_HOST} readelf -V -W ${TARGET_FOLDER}/openssl/lib/libssl.so|grep 'Name:'|grep OPENSSL|sed 's/_/./g'`
  # elf library versions are OPENSSL_1_1_1 hence changing _ to '.' for comparing
if [[ ! "${INSTALLED_SSL_VERSIONS}" =~ "OPENSSL.${OPENSSL_VERSION}" ]]; then
  install_openssl
fi

echo "* Check python"
INSTALLED_PYTHON_VERSION=`ssh ${TARGET_USER}@${TARGET_HOST} ${TARGET_FOLDER}/opt/python/bin/python3 --version`
if [[ "${INSTALLED_PYTHON_VERSION}" != "Python ${PYTHON_VERSION}" ]]; then
  install_python
fi

echo "* Check .venv"
INSTALLED_VENV=`ssh ${TARGET_USER}@${TARGET_HOST} \[\[ -f ${TARGET_FOLDER}/.venv/bin/python3 \]\] && echo 'ok'`
if [[ "${INSTALLED_VENV}" != "ok" ]]; then
  ssh ${TARGET_USER}@${TARGET_HOST} virtualenv -p "${TARGET_FOLDER}/opt/python/bin/python3" ${TARGET_FOLDER}/.venv
fi

echo "* Check dependencies"
ssh ${TARGET_USER}@${TARGET_HOST} "cd ${TARGET_FOLDER}; source ./.venv/bin/activate; pip install -r requirements-common.txt -r requirements-${ENVIRONMENT}.txt"

echo "* Run django migrations"
ssh ${TARGET_USER}@${TARGET_HOST} "cd ${TARGET_FOLDER}; source ./.venv/bin/activate; export DJANGO_SETTINGS_MODULE=dognews.settings.${ENVIRONMENT}; python3 manage.py migrate"

echo "* Run django collectstatic (files go in ${TARGET_FOLDER}/public as per Passenger)"
ssh ${TARGET_USER}@${TARGET_HOST} "cd ${TARGET_FOLDER}; source ./.venv/bin/activate; export DJANGO_SETTINGS_MODULE=dognews.settings.${ENVIRONMENT}; python3 manage.py collectstatic --noinput"

echo "* Check superuser is present"
if [[ "${ENVIRONMENT}" == "local" ]]; then
  EXISTS_SUPER_USER=`ssh ${TARGET_USER}@${TARGET_HOST} sqlite3 "${TARGET_FOLDER}/db.sqlite3" "'select username from auth_user where username=\"${SUPERUSER_NAME}\" and is_superuser=1'"`
  if [[ "${EXISTS_SUPER_USER}" != "adminz" ]]; then
    echo "* Creating superuser ${SUPERUSER_NAME}: please enter password"
    ssh -t ${TARGET_USER}@${TARGET_HOST} "cd ${TARGET_FOLDER}; source ./.venv/bin/activate; python manage.py createsuperuser --email ${SUPERUSER_EMAIL} --username ${SUPERUSER_NAME}"
  fi
fi

echo "* Create passenger wsgi configuration"
create_passenger_configuration
