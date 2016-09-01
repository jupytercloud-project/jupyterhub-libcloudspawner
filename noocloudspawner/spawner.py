"""RemoteSpawner implementation"""
import signal
import errno
import pwd
import os
import pipes
from subprocess import Popen, call

from tornado import gen

from jupyterhub.spawner import Spawner
from traitlets import (
    Instance, Integer, Unicode, List, Bool
)

from jupyterhub.utils import random_port
from jupyterhub.spawner import set_user_setuid

from celery.contrib import rdb

from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client
from keystoneclient import client as ksclient

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import SSHKeyDeployment


import random, string

import requests
import time
from time import sleep

class NooCloudSpawner(Spawner):
    """A Spawner that create notebook inside NooCloud."""

    noocloud_url = Unicode(
        "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens",
        config=True,
        help=''
    )
    noocloud_user = Unicode(
        config=True,
        help=''
    )
    noocloud_userpassword = Unicode(
        config=True,
        help=''
    )
    noocloud_project = Unicode(
        config=True,
        help=''
    )
    machine_size = Unicode(
        config=True,
        help=''
    )
    noocloud_region = Unicode(
        'RegionOne',
        config=True,
        help=''
    )
    machine_image = Unicode(
        config=True,
        help=''
    )
    machine_net = Unicode(
        config=True,
        help=''
    )
    machineid = Unicode(
        "",
        help=''
    )

    def getLibCloudDriver(self):
        """
            Retrieve LibCloudDriver 
        """
        cls = get_driver(Provider.OPENSTACK)
        driver = cls(self.noocloud_user, self.noocloud_userpassword,
                     ex_force_auth_version='3.x_password',
                     ex_force_auth_url=self.noocloud_url,
                     ex_force_service_region=self.noocloud_region,
                     ex_tenant_name=self.noocloud_project)
        return driver

    def getMachine(self, machineid):
        """
            Retrieve machine informations
        """
        self.log.debug("Getting Machine")
        driver = self.getLibCloudDriver()
        m = driver.ex_get_node_details(machineid)
        self.log.debug(m)
        return m
    
    def getMachineStatus(self):
        self.log.debug("Getting Machine status")
        machineinfos = self.getMachine(self.machineid)
        self.log.debug(machineinfos)
        if machineinfos:
            if machineinfos.state == 'running':
                self.log.debug("Machine runnig")
                return None
        self.log.debug("Machine NOT running")
        return 1

    def createMachine(self):
        """
            Create a machine, return machine informations
        """
        self.log.debug("Spawning machine")
        driver = self.getLibCloudDriver()

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
                   apitoken=self.get_env()["JPY_API_TOKEN"],
                   user=self.user.name,
                   cookiename=self.user.server.cookie_name,
                   baseurl=self.user.server.base_url,
                   hubprefix=self.hub.server.base_url,
                   apiurl=self.hub.api_url,
                   notebookargs="",
            )

        print(userdata)

        images = driver.list_images()
        sizes = driver.list_sizes()
        nets = driver.ex_list_networks()

        for i in images:
            if i.name == self.machine_image:
                self.log.debug("Image found %s" % i.name)
                machineimage = i
        for s in sizes:
            if s.name == self.machine_size:
                self.log.debug("Size found %s" % s.name)
                machinesize = s
        for n in nets:
            self.log.debug(n.name)
            if n.name == self.machine_net:
                self.log.debug("Network found %s" % n.name)
                machinenet = n

        randomstring = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))

        machinename = ("jpy-%s-%s" % (self.user.name, randomstring))
        node = driver.create_node(name=machinename,
                                  image=machineimage,
                                  size=machinesize,
                                  networks=[machinenet],
                                  ex_keyname="tristanlt",
                                  ex_userdata=userdata)
        self.log.debug(node)
        return node

    def load_state(self, state):
        """load machineid from state"""
        super(NooCloudSpawner, self).load_state(state)
        pass
    
    def get_state(self):
        """add machineid to state"""
        state = super(NooCloudSpawner, self).get_state()
        if self.machineid:
            state['machineid'] = self.machineid
        return state

    def clear_state(self):
        """clear pid state"""
        super(NooCloudSpawner, self).clear_state()
        self.machineid = u""

    @gen.coroutine
    def start(self):
        """Start the process"""
        self.log.debug("DEBUG start nooSpwaner")
        
        machine = self.createMachine()
        
        timeout_start = time.time()
        timeout = 30  # seconds
        
        cont = True
         
        while (time.time() < timeout_start + timeout) and cont:
            m = self.getMachine(machineid=machine.id)
            if m.state == "running":
                self.log.debug("Machine ready, updating Jupyter db")
                # Nice ! our instance is up and ready !
                self.user.server.port = 8000
                self.user.server.ip = m.private_ips[0]
                self.machineid = m.id
                cont = False
            sleep(1)
        self.db.commit()

    @gen.coroutine
    def poll(self):
        """Poll the process"""
        if self.machineid:
            return self.getMachineStatus()
        else:
            return 1

    @gen.coroutine
    def _signal(self, sig):
        """simple implementation of signal

        we can use it when we are using setuid (we are root)"""
        #try:
        #    os.kill(self.pid, sig)
        #except OSError as e:
        #    if e.errno == errno.ESRCH:
        #        return False # process is gone
        #    else:
        #        raise
        return True # process exists

    @gen.coroutine
    def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        driver = self.getLibCloudDriver()
        if not self.getMachineStatus():
            self.log.debug("Cloud instance running, send delete for %s " % self.machineid)
            m = self.getMachine(self.machineid)
            driver.destroy_node(m)
        return
