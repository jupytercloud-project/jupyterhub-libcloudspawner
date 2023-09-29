Installation & usage
====================

This documentation explains how to use LibcloudSpawner with JupyterHub. In this example, we used OpenStack cloud manager, which is currently the only supported manager.

Installation 
------------

>>> pip install apache-libcloud
>>> pip install Jinja2
>>> pip install jupyter-libcloudspawner

Spawner configuration
---------------------

First, configure LibcloudSpawner as your spawner in the Jupyterhub configuration file.

>>> c.JupyterHub.spawner_class = 'libcloudspawner.spawner.LibcloudSpawner'

Cloud configuration
-------------------

LibcloudSpawner will create, poll and destroy instance. It needs some information depending on your cloud provider. See examples, nodemanagers API documentation or LibCloud documentation (https://libcloud.readthedocs.io/en/latest/compute/drivers/openstack.html). 

Cloud parameters
++++++++++++++++

For instances, in this case, the cloud provider is OpenStack. User login and password which manage the instance are lops-jupyter and gloubiboulga. Authentication handshake uses Keystone v3 method and domain name is 'default'. Instances will be created in RegionOne.  

**libcloudparams** : Libcloud custom parameters 

>>> c.LibcloudSpawner.libcloudparams = {"arg_user_id": "lops-jupyter",
>>>                                    "arg_key": "secret",
>>>                                    "ex_force_auth_version": "3.x_password",
>>>                                    "ex_force_auth_url": "https://openstack.server.com:5000",
>>>                                    "ex_force_service_region": "RegionOne",
>>>                                    "ex_tenant_name": "noo-lops-jupyter",
>>>                                    "ex_domain_name": "default"}

.. note::

   Since Apache LibCloud use Keystone v2 password authentication as default, Keystone v3 users must set `ex_force_auth_version` parameter to `3.x_password`.
   
   In this case, please set also `ex_domain_name` to project domain.


Cloud Network
+++++++++++++

JupyterHub server and JupyterNotebook nodes will communicate on port 8000. Real users will not have any direct contact with cloud instances. In Access Groups or firewall, be sure JupyterHub server has access to nodes on port 8000. 

Common case is to configure your JupyterHub and JupyterNotebook nodes on the same private network, and associate floating IP address to the Hub. 

**userserver_net** : Network name where to connect the instance port.

>>> c.LibcloudSpawner.userserver_net = "private-net"

Region
++++++

**cloud_region** : Instance cloud region.

>>> c.LibcloudSpawner.cloud_region = "RegionOne"


Instance sizes (flavors)
------------------------

User can choose different instance sizes (aka instance flavor).

**userserver_sizes** : List of tuples like ("Display name", "cloud flavor name"). This list is presented to users as a form at spawn step. 

>>> c.LibcloudSpawner.userserver_sizes = [("1vcpu 2Go RAM", "m1.small"),
>>>                                    ("4vcpu 64Go RAM", "4c.extramem"),]

Instance images (templates)
---------------------------

User can choose different different instance images to the end user.

For example, administrator can provide an image dedicated to R language and another one dedicated to Python, or different operating systems.

**userserver_images** : List of tuples like ("Display name", "cloud template name"). This list is presented to users as a form before the spawn. 

>>> c.LibcloudSpawner.userserver_images = [("Default image","noo33u16-station-jpy-python")]

Instance images requirements
++++++++++++++++++++++++++++

LibcloudSpawner will use cloud-init scripts to configure and launch jupyterhub-singleuser service on instance. In order to start jupyterhub-singleuser server it insert a systemd unit that configures and starts Jupyterhub singleuser server.

We recommend that you prepare images with the software and working environments already pre-installed.

Note that cloud-init scripts can also install JupyterNotebook dependencies (Jupyter, ipython...), but this lengthens the spawning time.

Default userdata script can be used with Ubuntu cloudimage 22.04 and Debian cloud image.

Default script will :
 - configure apt repos
 - install pip, numpy and matplotlib via apt (if needed) 
 - create the user authenticated by jupyterhub (if needed)
 - install jupyter and jupyterhub via pip (if needed)
 - install jupyterhub-singleuser systemd unit
 - enable and start jupyterhub-singleuser

This userdata script is provided as an example and should be adapted to your case.

Please see customize section to adapt libcloudspawner as in your secret wishes. 