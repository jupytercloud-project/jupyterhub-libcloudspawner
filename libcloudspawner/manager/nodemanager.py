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

import random
import string
import socket
import datetime
import time

import jinja2

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from .errors import NetworkNotFoundError, ImageNotFoundError, SizeNotFoundError


class NodeManager(object):
    """ NodeManager have tools to connect with cloud,
    NodeManager create, audit and delete virtual machines
    """

    def __init__(self, spawner_conf, logguer):

        cls = self._get_provider()

        # Note : spawner_conf.libcloudparams can't be used as full **kwargs
        # because libcloud.compute.drivers.OpenStackNodeDriver should receive
        # user_id and key as **args and everything else as **kwargs...
        self.driver = cls(spawner_conf.libcloudparams['arg_user_id'],
                          spawner_conf.libcloudparams['arg_key'],
                          **spawner_conf.libcloudparams)

        self.logguer = logguer
        self.spawner_conf = spawner_conf
        self.node = None
        self.node_ip = None
        # TODO this parameter should be set by spawner_conf
        self.node_port = 8000
        # TODO this parameter should be set by spawner_conf
        self.timeout = 120

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
            self.logguer.debug("Can not retrieve node information \
            from cloud provider")

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
        self.logguer.debug("HTTP Notebook check @%s:%s" % (self.node_ip,
                                                           self.node_port))

        now = datetime.datetime.now()
        notafter = now + datetime.timedelta(seconds=self.timeout)

        conn_ok = False
        while datetime.datetime.now() < notafter:
            tictac = notafter - datetime.datetime.now() 
            self.logguer.debug("Trying connection @%s:%s (timeout %s)" % (
                                                        self.node_ip,
                                                        self.node_port,
                                                        tictac))

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

    def _check_notebook_nowait(self):
        """ Check for notebook
        """
        self.logguer.debug("HTTP Notebook check @%s:%s" % (self.node_ip,
                                                           self.node_port))
        try:
            socket.create_connection((self.node_ip, self.node_port), 3)
        except:
            return False
        return True

    def retrieve_node(self, id):
        """
        Search for node with id on cloud (used in load_state after jupyter kill)
        """
        try:
            self.node = self.driver.ex_get_node_details(id)
        except:
            self.logguer.debug("Can not retrieve node information \
            from cloud provider")

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
                if self._check_notebook_nowait():
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

        env = jinja2.Environment(
                          loader=jinja2.PackageLoader(
                                self.spawner_conf.userdata_template_module,
                                'data'))

        userdata_template = env.get_template(
                                self.spawner_conf.userdata_template_name)

        userdata = userdata_template.render(
                   apitoken=str(api_token),
                   user=username,
                   cookiename=self.spawner_conf.user.server.cookie_name,
                   baseurl=self.spawner_conf.user.server.base_url,
                   hubprefix=self.spawner_conf.hub.server.base_url,
                   apiurl=self.spawner_conf.hub.api_url,
                   notebookargs=self.spawner_conf.notebookargs)

        node_conf = {}

        # Search image
        imagename = self.spawner_conf.user_options['machineimage']
        node_conf['image'] = self._get_image(imagename)

        # Search size /flavor
        sizename = self.spawner_conf.user_options['machinesize']
        node_conf['size'] = self._get_size(sizename)

        # Search network
        netname = self.spawner_conf.machine_net
        node_conf['networks'] = [self._get_network(netname)]

        # Generate nodename
        node_conf['name'] = self._generate_machine_name(
                                    self.spawner_conf.user.name)

        node_conf['ex_userdata'] = userdata

        if "ex_keyname" in self.spawner_conf.libcloudparams.keys():
            node_conf['ex_keyname'] = self.spawner_conf.libcloudparams['ex_keyname']

        # Create machine
        self.node = self.driver.create_node(**node_conf)

        while True:
            time.sleep(1)
            self.get_node_status()
            self.logguer.debug(self.node)
            
            if self._check_notebook_nowait():
                self._update_node_net_informations()
                yield (self.node_ip, self.node_port)
            else:
                yield None