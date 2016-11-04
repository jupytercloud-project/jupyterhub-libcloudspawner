from tornado import gen

from jupyterhub.spawner import Spawner
from traitlets import (
    Instance, Integer, Unicode, List, Bool
)
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import random, string

import requests
import time
from time import sleep

import shlex

class LibcloudSpawner(Spawner):
    """A Spawner that create notebook inside NooCloud."""

    cloud_url = Unicode(
        "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens",
        config=True,
        help=''
    )
    cloud_user = Unicode(
        config=True,
        help=''
    )
    cloud_userpassword = Unicode(
        config=True,
        help=''
    )
    cloud_project = Unicode(
        config=True,
        help=''
    )
    machine_sizes = List(
        [],
        config=True,
        help=''
    )
    cloud_region = Unicode(
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
    forceuser = Unicode(
        "",
        config=True,
        help='Use this user instead of auth user'
    )
    notebookargs = Unicode(
        "",
        config=True,
        help='notebookargs'
    )

    def _options_form_default(self):
        formhtml=[]
        formhtml.append("<label for=\"args\"> Virtual machine size </label>")
        formhtml.append("<select name=\"size\">")
        for size in self.machine_sizes:
            option = "<option value=\"%s\"> %s </option>" % (size[1], size[0])
            formhtml.append(option)
        formhtml.append("</select>")
        return(" ".join(formhtml))

    def options_from_form(self, formdata):
        options = {}
        options['machinesize'] = ""

        machinesize = formdata.get('size', "")[0]
        options['machinesize'] = machinesize
        return options

    def get_args(self):
        """Return arguments to pass to the notebook server"""
        argv = super().get_args()
        if self.user_options.get('argv'):
            argv.extend(self.user_options['argv'])
        return argv

    def get_env(self):
        env = super().get_env()
        if self.user_options.get('env'):
            env.update(self.user_options['env'])
        return env

    def getLibCloudDriver(self):
        """
            Retrieve LibCloudDriver 
        """
        cls = get_driver(Provider.OPENSTACK)
        driver = cls(self.cloud_user, self.cloud_userpassword,
                     ex_force_auth_version='3.x_password',
                     ex_force_auth_url=self.cloud_url,
                     ex_force_service_region=self.cloud_region,
                     ex_tenant_name=self.cloud_project)
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
                # Machine running, trying http
                self.log.debug("Machine running. Trying HTTP request on 8000")
                try:
                    httptest = requests.head("http://%s:8000" % machineinfos.private_ips[0], max_retries=1)
                except:
                    httptest = None
                self.log.debug(httptest)
                return None
        self.log.debug("Machine NOT ready")
        return 1

    def createMachine(self):
        """
            Create a machine, return machine informations
        """
        self.log.debug("Spawning machine")
        driver = self.getLibCloudDriver()

        if self.forceuser:
            username = self.forceuser
        else:
            username = self.user.name

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
                   user=username,
                   cookiename=self.user.server.cookie_name,
                   baseurl=self.user.server.base_url,
                   hubprefix=self.hub.server.base_url,
                   apiurl=self.hub.api_url,
                   notebookargs=self.notebookargs,
            )

        self.log.debug(userdata)

        images = driver.list_images()
        sizes = driver.list_sizes()
        nets = driver.ex_list_networks()

        for i in images:
            if i.name == self.machine_image:
                self.log.debug("Image found %s" % i.name)
                machineimage = i
        for s in sizes:
            if s.name == self.user_options['machinesize']:
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
        super(LibcloudSpawner, self).load_state(state)
        pass

    def get_state(self):
        """add machineid to state"""
        state = super(LibcloudSpawner, self).get_state()
        if self.machineid:
            state['machineid'] = self.machineid
        return state

    def clear_state(self):
        """clear pid state"""
        super(LibcloudSpawner, self).clear_state()
        self.machineid = u""

    @gen.coroutine
    def start(self):
        """Start the process"""
        self.log.debug("DEBUG start libcloudSpawner")
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
                if len(m.private_ips) > 0:
                    self.user.server.ip = m.private_ips[0]
                if len(m.public_ips) > 0:
                    self.user.server.ip = m.public_ips[0]
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
    def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        driver = self.getLibCloudDriver()
        if not self.getMachineStatus():
            self.log.debug("Cloud instance running, send delete for %s " % self.machineid)
            m = self.getMachine(self.machineid)
            driver.destroy_node(m)
        return
