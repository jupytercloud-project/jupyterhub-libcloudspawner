Installation & usage
====================

This documentation explain how to use LibcloudSpawner with Jupyter Hub. In this example, we used OpenStack cloud manager, which is, at this time, the only supported Manager.

Installation 
------------

Since JupyterHub LibCloudSpawner wasn't publish on Pypi you must pip it directly from Github.

>>> pip install apache-libcloud
>>> pip install Jinja2
>>> pip install git+https://github.com/tristanlt/jupyter-libcloudspawner

Spawner configuration
---------------------

First, configure LibcloudSpawner as your spawner in Jupyterhub configuration file.

>>> c.JupyterHub.spawner_class = 'libcloudspawner.spawner.LibcloudSpawner'

Cloud configuration
-------------------

LibcloudSpawner will create, poll and destroy instance. It need some informations depending to your cloud provider. See examples, nodemanagers API documentation or LibCloud documentation (https://libcloud.readthedocs.io/en/latest/compute/drivers/openstack.html). 

Cloud parameters
++++++++++++++++

For instance, in this case, the cloud provider is an OpenStack cloud. Login and password of the user which manage instance are lops-jupyter and gloubiboulga. Authentication handshake used Keystone v3 method and domain name is 'default'. Instances will be create in RegionOne.  

**cloud_url** : Endpoint where connect to cloud provider

>>> c.LibcloudSpawner.cloud_url = "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens"

**cloud_user** : Cloud user which create and destroy instances 

>>> c.LibcloudSpawner.cloud_user = "lops-jupyter"

**cloud_userpassword** : Cloud user password

>>> c.LibcloudSpawner.cloud_userpassword = "gloubiboulga"

**cloud_project** : Project/tenant which own notebook instances 

>>> c.LibcloudSpawner.cloud_project = "noo-lops-jupyter"


**libcloudparams** : Libcloud customs parameters 

>>> c.LibcloudSpawner.libcloudparams = {"arg_user_id": "lops-jupyter",
>>>                                    "arg_key": "gloubiboulga",
>>>                                    "ex_force_auth_version": "3.x_password",
>>>                                    "ex_force_auth_url": "https://openstack.server.com/keystone/v3/auth/tokens",
>>>                                    "ex_force_service_region": "RegionOne",
>>>                                    "ex_tenant_name": "noo-lops-jupyter",
>>>                                    "ex_domain_name": "default",
>>>                                    "ex_keyname": "tristanlt"}

Cloud Network
+++++++++++++

JupyterHub server and JupyterNotebooks nodes will communicate on port 8000. Real users will not have any contact directly with cloud instances. In Access Groups or firewall, be sure JupyterHub server access nodes on port 8000. 

Common case is to configure your JupyterHub and JupyterNotebooks nodes on the same private network, and associate flotting IP address to Hub. 

**machine_net** : Name of network where to connect instance port.

>>> c.LibcloudSpawner.machine_net = "noo-net-33"

Region
++++++

**cloud_region** : Instance cloud region.

>>> c.LibcloudSpawner.cloud_region = "RegionOne"


Instance sizes (flavors)
------------------------

LibCloudSpawner allow JupyterHub administrator to propose different Notebook size (aka instance flavor) to final user. 

**machine_sizes** : List of tuples like ("Display name", "cloud flavor name"). This list was presented to users at spawner form. 

>>> c.LibcloudSpawner.machine_sizes = [("1vcpu 2Go RAM", "m1.small"),
>>>                                    ("4vcpu 64Go RAM", "4c.extramem"),]

Instance images (templates)
---------------------------

LibCloudSpawner allow JupyterHub administrator to propose different Notebook images to final user.

For instance, administrator can provision cloud project with one image dedicated to R language and one else dedicated to Python.

**machine_images** : List of tuples like ("Display name", "cloud template name"). This list was presented to users at spawner form.

>>> c.LibcloudSpawner.machine_images = [("Default image","noo33u16-station-jpy-python")]

Instance images requirements
++++++++++++++++++++++++++++

LibcloudSpawner will use cloud-init scripts to configure and launch jupyterhub-singleuser notebooks inside virtual machine. For instance, script can install system requirements, like jupyterhub and insert a systemd unit which configure and start Jupyter User Notebook.

Note that cloud-init can also setup JupyterNotebook dependencies (Jupyter, ipython...), but this make spawn time longer.

Default userdata script can be used with Ubuntu cloudimage Xenial 16.04 and Debian cloud image.

Default script will :
 - configure apt repos
 - install pip, numpy and matplotlib via apt (if needed) 
 - create the user authenticated by jupyterhub (if needed)
 - install jupyter and jupyterhub via pip (if needed)
 - install jupyterhub-singleuser systemd unit
 - enable and start jupyterhub-singleuser

This userdata script is provided as an example and should be adapted to your case.

Please see customize section to adapt libcloudspawner like in your secrets wish. 

Metrology
---------

**statsdparams** : if you wish have some metrics about usage

>>> c.LibcloudSpawner.statsdparams = {"host": "statds.server.com",
>>>                                   "port": 8125,
>>>                                   "prefix": "jhubdev"}