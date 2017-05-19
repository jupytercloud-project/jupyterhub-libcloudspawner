#!/usr/bin/env python
# _*_ coding : utf-8 _*_

""" nodemanager.py : jupyter-libcloudSpawner manager for notebook instance (node) 
"""
__author__ = "Tristan Le Toullec"
__copyright__ = "Copyright 2017, LOPS"
__credits__ = ["Tristan Le Toullec"]
__license__ = "CeCILL-B"
__maintainer__ = "Tristan Le Toullec"
__email__ = "tristan.letoullec@cnrs.fr"

from .errors import NetworkNotFoundError, ImageNotFoundError, SizeNotFoundError

import random
import string
import socket
import datetime
import time

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

class NodeManager(object):
    """ NodeManager have tools to connect with cloud,
    NodeManager create, audit and delete virtual machines
    """

    def __init__(self, spawner_conf, logguer):

        #cls = get_driver(Provider.OPENSTACK)
        cls = self._get_provider()

        self.driver = cls(spawner_conf.cloud_user,
                          spawner_conf.cloud_userpassword,
                          ex_force_auth_version='3.x_password',
                          ex_force_auth_url=spawner_conf.cloud_url,
                          ex_force_service_region=spawner_conf.cloud_region,
                          ex_tenant_name=spawner_conf.cloud_project)

        self.logguer = logguer
        self.spawner_conf = spawner_conf
        self.node = None
        self.node_ip = None
        self.node_port = 8000 # TODO this parameter should be set by spawner_conf
        self.timeout = 120 # TODO this parameter should be set by spawner_conf 

#         cls = self._get_provider()
# 
#         self.driver = cls(user=spawner_conf.cloud_user,
#                           password=spawner_conf.cloud_userpassword,
#                           ex_force_auth_version='3.x_password',
#                           ex_force_auth_url=spawner_conf.cloud_url,
#                           ex_force_service_region=spawner_conf.cloud_region,
#                           ex_tenant_name=spawner_conf.cloud_project,
#                           key=None)


    def _get_provider(self):
        return get_driver(Provider.OPENSTACK)

    def _generate_machine_name(self, username):
        """ Generate random name for node
            Machine name contain username
        """
        randomstring = ''.join(
                    random.choice(string.ascii_uppercase) for _ in range(6)
                    )
        return ("jhub-%s-%s" % (username, randomstring))

    def _get_image(self, imagename):
        """ Search image in cloud project
        """
        images = self.driver.list_images()

        for i in images:
            if i.name == imagename:
                self.logguer.debug("Image found %s" % i.name)
                return i
        # Image not found, raising an error
        raise ImageNotFoundError

    def _get_network(self, netname):
        """ Search net in cloud project
        """
        nets = self.driver.ex_list_networks()

        for n in nets:
            self.logguer.debug(n.name)
            if n.name == netname:
                self.logguer.debug("Network found %s" % n.name)
                return n
        # Network not found, raising an error
        raise NetworkNotFoundError

    def _get_size(self, sizename):
        """ Search size in cloud project
        """
        sizes = self.driver.list_sizes()

        for s in sizes:
            if s.name == sizename:
                self.logguer.debug("Size found %s" % s.name)
                return s

        # Size not found, raising an error 
        raise SizeNotFoundError

    def _update_node_cloudstate(self):
        """
        Update nodes status
        """
        try:
            self.node = self.driver.ex_get_node_details(self.node.id)
        except:
            self.logguer.debug("Can not retrieve node information from cloud provider")

    def _update_node_net_informations(self):
        """
        Get first public_ips or the first private_ips
        """
        node = self.get_node()
        if ([node.public_ips or node.private_ips]):
            self.node_ip = [node.public_ips or node.private_ips][0][0]
        else:
            self.node_ip = None

    def _check_notebook(self):
        """ Wait for notebook running by simply request host:port
            @param timeout: in seconds
            @return: True of False
        """
        self.logguer.debug("HTTP Notebook check @%s:%s" % (self.node_ip, self.node_port))

        now = datetime.datetime.now()
        notafter = now + datetime.timedelta(seconds=self.timeout)

        conn_ok = False
        while datetime.datetime.now() < notafter:
            self.logguer.debug("Trying connection @%s:%s" % (self.node_ip,
                                                             self.node_port))

            # Try to connect to notebook port
            try:
                socket.create_connection((self.node_ip, self.node_port), 3)
            except:
                time.sleep(1)
                continue
            # Node notebook port open : "feu patate!"
            self.logguer.debug("HTTP Notebook check @%s:%s is OK" % (self.node_ip, self.node_port))
            conn_ok = True
            break

        return conn_ok

    def get_node(self):
        """
        Return node after updating node informations from cloud provider
        @return node or None
        """
        self._update_node_cloudstate()
        return self.node

    def destroy_node(self):
        """
        Destroy node
        @return node or None
        """
        try:
            self.driver.destroy_node(self.node)
        except:
            print('Node destroy failed')

    def get_node_status(self):
        """
        Check that node and notebook are OK 
        @return None if ok, 1 else
        """
        node = self.get_node()
        if node:
            if node.state == 'running':
                # Node Ok, updating network informations
                self._update_node_net_informations()

                # Notebook ? Did you respond ?
                if self._check_notebook():
                    return None
                else:
                    return 1
        return 1

    def create_machine(self, api_token):
        """
            Create a machine, return machine informations
        """
        self.logguer.debug("create_machine start")

        if self.spawner_conf.forceuser:
            username = self.spawner_conf.forceuser
        else:
            username = self.spawner_conf.user.name

        userdata = """#!/bin/bash
cat <<EOF > /etc/systemd/system/jupyterhub-singleuser.service
[Unit]
Description=JupyterHub-singleuser instance
 
[Service]
User={user}
Environment=JPY_API_TOKEN={apitoken}
ExecStart=/usr/local/bin/jupyterhub-singleuser --port=8000 --ip=0.0.0.0 --user={user} --cookie-name={cookiename} --base-url={baseurl} --hub-prefix={hubprefix} --hub-api-url={apiurl}  {notebookargs} \$@
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart jupyterhub-singleuser.service
systemctl enable jupyterhub-singleuser.service
""".format(
                   apitoken=str(api_token),
                   user=username,
                   cookiename=self.spawner_conf.user.server.cookie_name,
                   baseurl=self.spawner_conf.user.server.base_url,
                   hubprefix=self.spawner_conf.hub.server.base_url,
                   apiurl=self.spawner_conf.hub.api_url,
                   notebookargs=self.spawner_conf.notebookargs,
            )

        # Search image
        imagename = self.spawner_conf.user_options['machineimage']
        machineimage = self._get_image(imagename)

        # Search size /flavor
        sizename = self.spawner_conf.user_options['machinesize']
        machinesize = self._get_size(sizename)

        # Search network
        netname = self.spawner_conf.machine_net
        machinenet = self._get_network(netname)

        # Generate nodename
        nodename = self._generate_machine_name(self.spawner_conf.user.name)

        # Create machine
        node = self.driver.create_node(name=nodename,
                                       image=machineimage,
                                       size=machinesize,
                                       networks=[machinenet],
                                       ex_userdata=userdata)

        # Wait machine state==running
        # ! this method return an array of (one) nodes
        self.logguer.debug("CreateMachine waiting state==running")
        nodesok = self.driver.wait_until_running([node],
                                                 wait_period=1,
                                                 timeout=self.timeout)

        if nodesok:
            self.logguer.debug("CreateMachine node is running, checking user notebook")
            self.node = nodesok[0][0]

            self._update_node_net_informations()

            if self._check_notebook():
                return True
            else:
                return False
        else:
            self.logguer.debug("CreateMachine node not running after timeout")
            return False