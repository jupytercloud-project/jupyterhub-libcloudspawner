Installation & usage
====================

This documentation explains how to use LibcloudSpawner with Jupyter Hub. In this example, we used OpenStack cloud manager, which is currently the only supported manager.

Installation 
------------

Since JupyterHub LibCloudSpawner has not been published on Pypi, you must pip it directly from Github.

>>> pip install apache-libcloud
>>> pip install Jinja2
>>> pip install git+https://github.com/tristanlt/jupyter-libcloudspawner

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

**cloud_url** : Endpoint to connect to the cloud provider

>>> c.LibcloudSpawner.cloud_url = "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens"

**cloud_user** : Cloud user who creates and destroys instances 

>>> c.LibcloudSpawner.cloud_user = "lops-jupyter"

**cloud_userpassword** : Cloud user password

>>> c.LibcloudSpawner.cloud_userpassword = "secret"

**cloud_project** : Project/tenant which owns notebook instances 

>>> c.LibcloudSpawner.cloud_project = "noo-lops-jupyter"


**libcloudparams** : Libcloud custom parameters 

>>> c.LibcloudSpawner.libcloudparams = {"arg_user_id": "lops-jupyter",
>>>                                    "arg_key": "secret",
>>>                                    "ex_force_auth_version": "3.x_password",
>>>                                    "ex_force_auth_url": "https://openstack.server.com/keystone/v3/auth/tokens",
>>>                                    "ex_force_service_region": "RegionOne",
>>>                                    "ex_tenant_name": "noo-lops-jupyter",
>>>                                    "ex_domain_name": "default",
>>>                                    "ex_keyname": "tristanlt"}

Cloud Network
+++++++++++++

JupyterHub server and JupyterNotebook nodes will communicate on port 8000. Real users will not have any direct contact with cloud instances. In Access Groups or firewall, be sure JupyterHub server has access to nodes on port 8000. 

Common case is to configure your JupyterHub and JupyterNotebook nodes on the same private network, and associate floating IP address to the Hub. 

**machine_net** : Network name where to connect the instance port.

>>> c.LibcloudSpawner.machine_net = "noo-net-33"

Region
++++++

**cloud_region** : Instance cloud region.

>>> c.LibcloudSpawner.cloud_region = "RegionOne"


Instance sizes (flavors)
------------------------

LibCloudSpawner allows JupyterHub administrator to offer different Notebook sizes (aka instance flavor) to the end user. 

**machine_sizes** : List of tuples like ("Display name", "cloud flavor name"). This list is presented to users as a form before the spawn. 

>>> c.LibcloudSpawner.machine_sizes = [("1vcpu 2Go RAM", "m1.small"),
>>>                                    ("4vcpu 64Go RAM", "4c.extramem"),]

Instance images (templates)
---------------------------

LibCloudSpawner allows JupyterHub administrator to offer different Notebook images to the end user.

For example, administrator can provide a cloud project with an image dedicated to R language and another one dedicated to Python.

**machine_images** : List of tuples like ("Display name", "cloud template name"). This list is presented to users as a form before the spawn. 

>>> c.LibcloudSpawner.machine_images = [("Default image","noo33u16-station-jpy-python")]

Instance images requirements
++++++++++++++++++++++++++++

LibcloudSpawner will use cloud-init scripts to configure and launch jupyterhub-singleuser notebooks inside virtual machine. For instance, script can install system requirements, such as jupyterhub and insert a systemd unit that configures and starts Jupyter User Notebook.

Note that cloud-init can also setup JupyterNotebook dependencies (Jupyter, ipython...), but this lengthens the spawning time.

Default userdata script can be used with Ubuntu cloudimage Xenial 16.04 and Debian cloud image.

Default script will :
 - configure apt repos
 - install pip, numpy and matplotlib via apt (if needed) 
 - create the user authenticated by jupyterhub (if needed)
 - install jupyter and jupyterhub via pip (if needed)
 - install jupyterhub-singleuser systemd unit
 - enable and start jupyterhub-singleuser

This userdata script is provided as an example and should be adapted to your case.

Please see customize section to adapt libcloudspawner as in your secret wishes. 

Metrology
---------

**statsdparams** : if you wish to have some metrics about usage.

>>> c.LibcloudSpawner.statsdparams = {"host": "statds.server.com",
>>>                                   "port": 8125,
>>>                                   "prefix": "jhubdev"}
