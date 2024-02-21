# Configuration

This section explains how to configure JupyterHub and libcloudspawner.

We assume that you have already completed the [Cloud Preparation](prepare-cloud.md) and [Installation](install.md) sections.

## JupyterHub base

Generate default configuration
```
mkdir $HOME/jupyterhub
cd $HOME/jupyterhub
jupyterhub --generate-config
```

Configure IP and URL with internal private `ip`.
```python
c.JupyterHub.base_url = '/'
c.JupyterHub.bind_url = 'http://:8000'
c.JupyterHub.hub_bind_url = 'http://10.42.0.92:8081'
c.JupyterHub.hub_connect_url = 'http://10.42.0.92:8081'
c.JupyterHub.hub_ip = '10.42.0.92'
c.JupyterHub.hub_port = 8081
```

## Spawner configuration

First, configure LibcloudSpawner as your spawner in the Jupyterhub configuration file.

```python
c.JupyterHub.spawner_class = 'libcloudspawner.spawner.LibcloudSpawner'
```

Adjust timeout, it can take a long time to create an instance
```
c.Spawner.start_timeout = 120
c.Spawner.start_timeout = 600
c.Spawner.http_timeout = 60
```

Fix the userserver port
```
c.Spawner.port = 8666
```

## Cloud configuration

LibcloudSpawner will create, poll and destroy instance. It needs some information depending on your cloud provider.

See examples, nodemanagers API documentation or LibCloud documentation (https://libcloud.readthedocs.io/en/latest/compute/drivers/openstack.html). 

### Cloud parameters

For instances, in this case, the cloud provider is OpenStack. User login and password which manage the instance are lops-jupyter and gloubiboulga. Authentication handshake uses Keystone v3 method and domain name is 'default'. Instances will be created in RegionOne.  

**libcloud_driver_params** : Libcloud custom parameters

```
c.LibcloudSpawner.libcloud_driver_params = {"arg_user_id": "78648b209db34ed7a60724c69c234ae2",
                                   "arg_key": "YUTHdmRIO04Cdq7-6TehYxjYoLAibKEt0hMjBZeTcpOZrAJXGkkj9CnFBJboDbGAJEPWil6H6BJb6Jy247ECZQ",
                                   "ex_force_auth_version": "3.x_appcred",
                                   "ex_force_auth_url": "https://openstack.server.com:5000",
                                   "ex_force_service_region": "RegionOne",
                                   "ex_tenant_name": "myproject",
                                   "ex_domain_name": "default"}
```

### Cloud Network

JupyterHub server and JupyterNotebook nodes will communicate on port 8000. Real users will not have any direct contact with cloud instances. In Access Groups or firewall, be sure JupyterHub server has access to nodes on port 8000. 

Common case is to configure your JupyterHub and JupyterNotebook nodes on the same private network, and associate floating IP address to the Hub. 

**userserver_net** : Network name where to connect the instance port.

```python
c.LibcloudSpawner.userserver_net = "private-net"
```

### Instance sizes (flavors)

User can choose different instance sizes (aka instance flavor).

**userserver_sizes** : List of tuples like ("Display name", "cloud flavor name"). This list is presented to users as a form at spawn step. 

```
c.LibcloudSpawner.userserver_sizes = [("1vcpu 2Go RAM", "m1.small"),
                                      ("4vcpu 64Go RAM", "4c.extramem"),]
```

### Instance images (templates)

User can choose different different instance images to the end user.

For example, administrator can provide an image dedicated to R language and another one dedicated to Python, or different operating systems.

**userserver_images** : List of tuples like ("Display name", "cloud template name"). This list is presented to users as a form before the spawn. 

```
c.LibcloudSpawner.userserver_images = [("Default image","noo33u16-station-jpy-python")]
```

### Keyname

**userserver_keyname** : Name of the public key to insert into userserver (useful to debug).

```
c.LibcloudSpawner.userserver_keyname= "sysadmin"
```


## Ready ? try !

Launch Jupyterhub

```
jupyterhub -f jupyterhub_config.py
```

Point your browser to [http://*jupyterhub_floating_ip*:8000](http://*jupyterhub_floating_ip*:8000) 