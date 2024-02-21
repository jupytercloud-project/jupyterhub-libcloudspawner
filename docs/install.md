# Install libcloudSpawner

This documentation explains how to use LibcloudSpawner with JupyterHub. In this example, we used OpenStack cloud manager, which is currently the only supported manager.

## Requirements

This documentation assumes you have already some knowledge about Jupyter and JupyterHub.

* Linux instance for JupyterHub
* Python environnement (venv, conda...)
* Python install tool `pip`

## Installation

On your Jupyterhub instance, install dependencies and **jupyter-libcloudspawner** from Pypi.

```
pip install jupyterhub
pip install apache-libcloud
pip install Jinja2
pip install jupyter-libcloudspawner
```