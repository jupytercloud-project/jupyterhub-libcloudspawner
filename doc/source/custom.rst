Customize instance
==================

Here some informations about tunning and tweaking libcloudspawner. 

Best (in term of spawn time) is to customize instances images used by JupyterHub. But certain operations must be execute at instanciation time bu userdata script. 

Note that you can use vendor generics cloud images but JupyterHub requirements should be installs at instance startup. For final users, startup should take a while (depending on your cloud provider).  

Provide a custom userdata script
--------------------------------

Userdata scripts configure instance at first boot to configure and launch notebooks.

LibcloudSpawner search Jinja2 template of userdata script inside a Python module.

LibcloudSpawner will search templates inside **data** folder of the module designed by **spawner_conf.userdata_template_module** configuration.  

This module should be in JupyterHub's Python PYTHONPATH.

>>> c.spawner_conf.userdata_template_module = 'acmejhubcustoms'

Inside this **data** folder, LibcloudSpawner search for template designed by **spawner_conf.userdata_template_name**.

>>> c.spawner_conf.userdata_template_name = 'acme-userdata.yaml.j2'

Create your module
++++++++++++++++++

>>> mkdir acmejhubcustoms
>>> touch acmejhubcustoms/__init__.py
>>> mkdir acmejhubcustoms/data

.. note:
	Keep this module inside JupyterHub path. 

Create your first userdata Jinja2 template
++++++++++++++++++++++++++++++++++++++++++

Your template will receive some informations from LibcloudSpawner :
 - jhub_env (dict) : Environnements variables from JupyterHub 
 - user (string) : Authenticated user name
 - notebookargs (string) : from JupyterHub configuration
 - user_options_from_form (dict) : Selected options from final user
 
This simplest userdata template we can write ( name : _acmejhubcustoms/data/jhub.sh.j2_ )
(implies JupyterHub was already installed on template image and authenticated user exist on instance)

.. code-block:: bash

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

