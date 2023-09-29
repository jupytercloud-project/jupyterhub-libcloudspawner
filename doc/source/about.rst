About LibCloudSpawner
=====================

LibcloudSpawner is a JupyterHub Spawner that allow to launch singleuser-server on cloud instance. Each Jupyterhub user have a fresh cloud instance for his usage.

*This middleware is fully Kubernetes free.*

LibcloudSpawner is based on Apache Libcloud which provides an abstraction API for a lot of cloud providers. By the way, LibcloudSpawner support only OpenStack.

Supported cloud provider (PR are open) :

.. image:: _static/openstack-compat.png
   :width: 200px
   :alt: OpenStack Compatiblity 
   :align: center


Benefits :
* just need an instance for JupyterHub server, users ressources are dynamic
* single-user servers are full system, feel free to integrate them in your network (authentication, mountpoint, CephFS... )
* direct access to VT-io or pci-passthrough devices (GPU)
* run others services beside user JupyterHub single-server (VNC, RStudio...)
* no need Kubernetes nor Docker (but you can use it)

Drawbacks :
* user server could be very slow to start (depending cloud provider)
* no need Kubernetes nor Docker

.. image:: _static/general-usage.png
   :width: 600px
   :alt: LibcloudSpawner usage 
   :align: center
   
Internal
--------

.. image:: _static/flow-diagram.png
   :width: 600px
   :alt: Flow Diagram
   :align: center
