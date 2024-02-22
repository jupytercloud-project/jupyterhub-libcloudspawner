# About LibCloudSpawner

[![Chat on Gitter](https://img.shields.io/badge/Chat%20on-Gitter-green.svg)](https://gitter.im/jupyter-libcloudspawner/community)

LibcloudSpawner enables JupyterHub to spwan single-user notebooks server inside fresh cloud instance.

LibcloudSpawner is based on [Apache Libcloud](https://libcloud.apache.org/) which aims to provide an abstraction API for a lot of cloud providers. Apache Libcloud provides the ability to manage resources in AWS, Google Cloud or Azure. **But for the moment, only OpenStack is supported**.

## Overview

A [Jupyterhub Spawner](https://jupyterhub.readthedocs.io/en/stable/reference/spawners.html) start each single-user notebook server. LibcloudSpawner is a spawner that operate with cloud API to manage singleuser notebook server instance life-cycle. Each Jupyterhub user will have one cloud instance for his usage.

### Benefits

* needs one small instance for JupyterHub server, all other resources are dynamic
* single-user servers have real OS, feel free to integrate them in your information system (ActiveDirectory, authentication, mountpoint...)
* simple access to VT-io or pci-passthrough devices (GPU)
* ability to host third-party services on user instance (VNC, RStudio...)
* no need for Docker or Kubernetes

### Drawbacks

* user server could be very slow to start (depending cloud provider and image size)
* no need for Docker or Kubernetes

[See the full documentation for informations, use-case and tutorials](https://jupyter-libcloudspawner.readthedocs.io/en/latest/)