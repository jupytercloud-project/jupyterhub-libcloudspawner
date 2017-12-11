Libcloud Spawner installation & usage
=====================================

This documentation show how to user LibcloudSpawner with Jupyter Hub. In this example, we used OpenStack cloud manager, which is, at this time, the only supported Manager.

Installation 
------------

Since JupyterHub LibCloudSpawner wasn't publish on Pypi you must pip it directly from Github.

>>> virtualenv -p python3 jupyterhub_oncloud
>>> source jupyterhub_oncloud/bin/activate
>>> pip install jupyterhub
>>> pip install git+https://github.com/tristanlt/jupyter-libcloudspawner

Instance template/image requirements
------------------------------------

Libcloud will use a cloud-init script inserted at instance creation time, this script insert a systemd unit which configurer and start Jupyter User Notebook.

Note that cloud-init can also setup JupyterNotebook dependencies (Jupyter, ipython...), but this make spawn time longer.

Templates should have :

 - Systemd init
 - Jupyter Python package
 - Same users as the JupyterHub server (or auth)

Network access requirements
---------------------------

JupyterHub server and JupyterNotebooks nodes will communicate on port 8000. Real users will not have any contact directly with cloud nodes.

In Access Groups or firewall, be sure JupyterHub server access nodes on port 8000. 

Common case is to configure your JupyterHub and JupyterNotebooks nodes on the same private network, and associate flotting IP address to Hub.    


JupyterHub Configuration
------------------------

You need some informations about your Cloud Environnement :

- Informations about your cloud tenant
   - Username
   - Password
   - Tenant/project name
   - Tenant Network name (this network must be accessible from hub)
   - Which Region to use
   - Auth mode (see LibCloud docuementation or examples)
- Information about notebook node templates
   - Name(s) of template(s)
- Informations about allowed flavors
   - Name(s) of flavor(s)

JupyterHub spawner is configured inside JupyterHub global configuration.

Machine sizes (flavors)
+++++++++++++++++++++++

**machine_sizes** 

List of tuples like ("Display name", "cloud flavor name"). This list was presented to users at spawner form. 

>>> c.LibcloudSpawner.machine_sizes = [("1vcpu 2Go RAM", "m1.small"),
>>>                                    ("4vcpu 8Go RAM", "m1.large"),
>>>                                    ("2vcpu 32Go RAM", "2c.bigmem"),
>>>                                    ("8vcpu 32Go RAM", "8c.bigmem"),
>>>                                    ("4vcpu 64Go RAM", "4c.extramem"),]

**machine_images** 

List of tuples like ("Display name", "cloud template name"). This list was presented to users at spawner form.

>>> c.LibcloudSpawner.machine_images = [("Default image","noo33u16-station-jpy-python")]

**machine_net** 

Name of network where to connect instance port

>>> c.LibcloudSpawner.machine_net = "noo-net-33"

**cloud_region** 

Cloud region where place instance 

>>> c.LibcloudSpawner.cloud_region = "RegionOne"

**libcloudparams** 

 Certainly the most important parameters. See examples, nodemanagers API documentation or LibCloud documentation (https://libcloud.readthedocs.io/en/latest/compute/drivers/openstack.html).

>>> c.LibcloudSpawner.libcloudparams = {"arg_user_id": "lops-jupyter",
>>>                                    "arg_key": "gloubiboulga",
>>>                                    "ex_force_auth_version": "3.x_password",
>>>                                    "ex_force_auth_url": "https://openstack.server.com/keystone/v3/auth/tokens",
>>>                                    "ex_force_service_region": "RegionOne",
>>>                                    "ex_tenant_name": "noo-lops-jupyter",
>>>                                    "ex_domain_name": "default",
>>>                                    "ex_keyname": "tristanlt"}

**statsdparams** if you wish have some metrics about usage

>>> c.LibcloudSpawner.statsdparams = {"host": "statds.server.com",
                                  "port": 8125,
                                  "prefix": "jhubdev"}

**notebookargs**

These arguments added to user JupyterNotebook command line (inside systemd unit)

>>> c.LibcloudSpawner.notebookargs = "--notebook-dir=~"

  
Example Configuration
---------------------

>>> c.LibcloudSpawner.cloud_url = "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens"
>>> c.LibcloudSpawner.cloud_user = "lops-jupyter"
>>> c.LibcloudSpawner.cloud_userpassword = "snip-snip"
>>> c.LibcloudSpawner.cloud_project = "noo-lops-jupyter"
>>> c.LibcloudSpawner.machine_sizes = [("1vcpu 2Go RAM", "m1.small"),
>>>        ("4vcpu 8Go RAM", "m1.large"),
>>>        ("2vcpu 32Go RAM", "2c.bigmem"),
>>>        ("8vcpu 32Go RAM", "8c.bigmem"),
>>>        ("4vcpu 64Go RAM", "4c.extramem"),]
>>> c.LibcloudSpawner.machine_images = [("Default image","noo33u16-station-jpy-python")]
>>> c.LibcloudSpawner.machine_net = "noo-net-33"
>>> c.LibcloudSpawner.cloud_region = "RegionOne"
>>> c.LibcloudSpawner.libcloudparams = {"arg_user_id": "lops-jupyter",
>>>                                    "arg_key": "therisnothinghere",
>>>                                    "ex_force_auth_version": "3.x_password",
>>>                                    "ex_force_auth_url": "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens",
>>>                                    "ex_force_service_region": "RegionOne",
>>>                                    "ex_tenant_name": "noo-lops-jupyter",
>>>                                    "ex_domain_name": "default",
>>>                                    "ex_keyname": "tristanlt"}
>>> c.LibcloudSpawner.notebookargs = "--notebook-dir=~"


