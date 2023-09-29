#!/usr/bin/env python
# _*_ coding : utf-8 _*_

""" spwaner.py : jupyter-libcloudSpawner Spawner Class loaded by JupyterHub
"""

__author__ = "Tristan Le Toullec"
__copyright__ = "Copyright 2017, LOPS"
__credits__ = ["Tristan Le Toullec"]
__license__ = "CeCILL-B"
__maintainer__ = "Tristan Le Toullec"
__email__ = "tristan.letoullec@cnrs.fr"

import requests
import time
import asyncio

from tornado import gen
from jupyterhub.spawner import Spawner
from traitlets import (
    Instance, Integer, Unicode, List, Bool, Dict
)
import jinja2

from libcloudspawner.manager.nodemanager import NodeManager


class LibcloudSpawner(Spawner):
    """A Spawner that create cloud instance for JupyterHub single-user server (machine)."""

    #: Module where libcloudspawner can find a jinja2 template folder for :
    #: cloud-init script for machine instanciation 
    #: template for JupyterHub server UI (eg. options_form)
    userdata_template_module = Unicode(
        'libcloudspawner',
        config=True
    )
    #: Template name for cloud-init userdata script (instance customisation)
    userdata_template_name = Unicode(
        'userdata.sh.j2',
        config=True
    )
    #: List of tuple for machine instance flavors, final user will be able to choose (options_form)
    #:
    #: >>>  [('Simple machine', 's0-small'),
    #: >>>   ('Mouhahaha machine','h4-bigmem')]
    #:
    #: (required for Openstack)
    machine_sizes = List(
        [],
        config=True,
    )
    #: List of tuple for nodes images (templates)
    #:
    #: >>> [('Python jupyterhub', 'python-jupyter'),
    #: >>>  ('Jupyterlab beta','try-lab')]
    #:
    #: (required for Openstack)'
    machine_images = List(
        [],
        config=True
    )
    #: Network name where connect machine instance
    #:
    #: (required for Openstack)
    machine_net = Unicode(
        config=True
    )

    #: SSH Keyname 
    #:
    #: ssh key to insert in instance at cloudinit step
    keyname = Unicode(
        False,
        config=True
    )


    #: Instance Cloud node identifier (internal)
    machineid = Unicode(
        ""
    )
    #: Force unix username on machine (default is JupyterHub server authed user)
    #:
    #: Usefull if JupyterHub authenticated unix user doesn't existe on instance.
    #: For instance, on a fresh Ubuntu cloud image, we can set 'ubuntu'.
    #:
    #: This user must exist on machine instance
    forceuser = Unicode(
        "",
        config=True
    )
    #: Libcloud Parameters, see managers documentations for details
    libcloud_driver_params = Dict(
        {},
        config=True,
        help='LibCloud Driver params'
    )

    spawner_events = []

    def __init__(self, **kwargs):
        super(LibcloudSpawner, self).__init__(**kwargs)

        self.nodemanager = NodeManager(self,
                                       logguer=self.log)

        self.user_options_from_form = None

    def _options_form_default(self):
        """ These options are set by final user in an HTML form
            Users choices are passed to spawner in self.user_options
        """

        env = jinja2.Environment(loader = jinja2.PackageLoader(
            self.userdata_template_module, 'data'))

        options_form_template = env.get_template("options_form.html.j2")

        options_form_html = options_form_template.render(
            machine_images=self.machine_images,
            machine_sizes=self.machine_sizes)

        return(options_form_html)

    def options_from_form(self, formdata):
        """ Receive data from options_form
        Spawner need machinesize and machineimage

        Other options are stored in self.user_options_from_form for hacking
        ( ie : use theses customs options inside usedata template ) 
        """
        # These options are important for spawner
        options = {} 
        options['machinesize'] = ""
        options['machineimage'] = ""
        machineimage = formdata.get('machineimage', "")[0]
        machinesize = formdata.get('machinesize', "")[0]
        options['machineimage'] = machineimage
        options['machinesize'] = machinesize

        # Store formdata for customs usages
        self.user_options_from_form = formdata

        return options

    def get_args(self):
        """
            Return arguments to pass to the notebook server
        """
        argv = super().get_args()
        if self.user_options.get('argv'):
            argv.extend(self.user_options['argv'])
        return argv

    def get_env(self):
        env = super().get_env()
        if self.user_options.get('env'):
            env.update(self.user_options['env'])
            print(env)
        return env

    def load_state(self, state):
        """
            Getting server ID and port from state
            Try to recover single server access
        """
        super(LibcloudSpawner, self).load_state(state)

        if not state:
            pass

        if 'machineid' in state.keys():
            if 'serverport' in state.keys():
                # Call NodeManager to search instance by instance ID
                try:
                    self.nodemanager.retrieve_node(state['machineid'])
                except:
                    self.log.info("Instance %s from state not found, clearing state." % state['machineid'])
                    self.clear_state()
                    return
                self.nodemanager.node_port = state['serverport']
                #self.machineid = state['machineid']
        pass

    def get_state(self):
        """
            Add machineid to state
            machineid : Cloud instance id
            serverport : Jupyter single notebook port
        """
        state = super(LibcloudSpawner, self).get_state()
        if self.nodemanager.node:
            state['machineid'] = self.nodemanager.node.id
            state['serverport'] = self.server.port
            self.log.debug('SpawnerStateMgmt get_state storing : %s %s' % (state['machineid'],state['serverport']))
        return state

    def clear_state(self):
        """
            Clear machine from states
        """
        super().clear_state()

    async def progress(self):
        """Async generator for progress events
        Send event on :
        * image, net and flavor requests
        * node creation
        * jhub port recheable
        """
        self.log.debug('progress called')
        event_index = 0
        while True:
            #events = self.nodemanager.node_events
            #if event_index < (len(events)):
            #    current_event = events[event_index]
            #    event_index += 1
            #    print(self.nodemanager.node_events)
            #    self.log.debug(f'progress {event_index}')
            current_event={"progress": 42, "message": "Hello world!", "ready": False}
            yield current_event
            await asyncio.sleep(1)

    #@gen.coroutine
    async def start(self):
        """
            Start notebook node and poll machine until timeout
        """
        jhub_env = {}
        # Keeping only env related to Jupyter (exclude PATH, LANG...)
        for key, value in self.get_env().items():
            if ("JUPYTER" in key) or ("JPY" in key):
                jhub_env[key]=value

        # Retrieve user args to provide to Jupyter (from option form)
        notebook_args = self.get_args()

        # Server port
        # 0 : random
        # != 0 : set by configuration
        if self.port == 0:
            server_port = self.server.port
        else:
            server_port = self.port

        # Node creation
        await self.nodemanager.create_machine(jhub_env,
                                        notebook_args,
                                        self.user_options_from_form,
                                        server_port)
        startup_poll_interval = 1.
        timeoutloop = int(self.start_timeout / startup_poll_interval)
        for i in range(self.start_timeout):
            status = await self.poll()
            if status is None:
                # Notebook ready
                self.user.server.ip = self.nodemanager.node_ip
                self.user.server.port = self.nodemanager.node_port
                self.machineid = self.nodemanager.node.id
                self.log.info("Jupyter singleuser-server responding at %s:%s (%s)" % 
                              (self.user.server.ip,
                               self.user.server.port,
                               self.machineid))
                self.db.commit()
                return(self.user.server.ip,
                       self.user.server.port)
            await gen.sleep(startup_poll_interval)
        # Timeout start failed...
        self.log.debug("Spawn Timeout, deleting Cloud instance %s ")
        self.nodemanager.destroy_node()

    async def poll(self):
        """
            Poll the node and singleserver status
        """
        status = await self.nodemanager.get_node_status()
        return status

    async def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        await self.nodemanager.destroy_node()
        return
