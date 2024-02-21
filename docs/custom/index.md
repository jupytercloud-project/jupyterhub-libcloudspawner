# Customize libcloudSpawner

Here is some information about tuning and tweaking libcloudspawner. 

The best way (in terms of spawn time) is to customize instances images used by JupyterHub. But some operations must be executed at instantiation time by a cloud-init userdata script.

Note that you can use generic vendors cloud images but JupyterHub requirements should be installed at the start of the instance. For end users, startup should take some time (depending on your cloud provider).  

## Provide a custom userdata script

Userdata scripts configure instance at first startup to customize and launch Jupyterhub singleuser service.

LibcloudSpawner searches for a Jinja2 template of userdata script inside a Python module.

LibcloudSpawner will search templates inside **data** folder of the module designed by **c.LibcloudSpawner.userdata_template_module** configuration.  

This module should be in JupyterHub's Python PYTHONPATH.

```
c.spawner_conf.userdata_template_module = 'acmejhubcustoms'
```

Inside this **data** folder, LibcloudSpawner searches for a template designed by **c.LibcloudSpawner.userdata_template_name**.

```
c.spawner_conf.userdata_template_name = 'acme-userdata.yaml.j2'
```

## Create your module

```
mkdir acmejhubcustoms
touch acmejhubcustoms/__init__.py
mkdir acmejhubcustoms/data
```

You should copy LibcloudSpawner default templates to this folder https://github.com/tristanlt/jupyter-libcloudspawner/tree/master/libcloudspawner/data

!!! note

	Keep this module inside JupyterHub path. 

### Create your first userdata Jinja2 template

Your template will receive some information from LibcloudSpawner :

* jhub_env (dict) : Variable environments from JupyterHub 
* user (string) : Authenticated user name
* notebookargs (string) : From JupyterHub configuration
* user_options_from_form (dict) : Selected options by end user
 
This is the simplest userdata template we can write ( name : _acmejhubcustoms/data/jhub.sh.j2_ )
(implies JupyterHub is already installed on the template image and that an authenticated user exists in the instance)

```bash
	#!/bin/bash
	# Create systemd service
	cat <<EOF> /etc/default/jupyter
	{% for key, value in jhub_env.items() %}
	{{key}}={{value}}
	{% endfor %}
	EOF
	
	# Search pre-installed jupyterhub 
	JHUB_SINGLEUSER=`/usr/bin/which jupyterhub-singleuser`
	
	# Create system service
	cat <<EOF > /etc/systemd/system/jupyterhub-singleuser.service
	[Unit]
	Description=JupyterHub-singleuser instance
	 
	[Service]
	User={{ user }}
	EnvironmentFile=/etc/default/jupyter
	ExecStart=${JHUB_SINGLEUSER} --port=8000 --ip=0.0.0.0 {{ notebookargs }} \$@
	[Install]
	WantedBy=multi-user.target
	EOF
	
	# Reload systemd commands
	# Start and enable service 
	systemctl daemon-reload
	systemctl restart jupyterhub-singleuser.service
	systemctl enable jupyterhub-singleuser.service
```