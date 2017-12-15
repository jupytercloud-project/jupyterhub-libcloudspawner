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

from tornado import gen
from jupyterhub.spawner import Spawner
from traitlets import (
    Instance, Integer, Unicode, List, Bool, Dict
)
import jinja2

from libcloudspawner.manager.nodemanager import NodeManager
from statsd import StatsClient


class LibcloudSpawner(Spawner):
    """A Spawner that create notebook inside NooCloud."""

    #: Cloud API url (auth)
    #:
    #: ie: https://controler:5000/v3/auth/tokens
    #: 
    #: (required for: Openstack)
    cloud_url = Unicode(
        "https://noocloud.univ-brest.fr/keystone/v3/auth/tokens",
        config=True
    )
    #: Cloud username to manage nodes
    #:
    #: (required for: Openstack)
    cloud_user = Unicode(
        config=True
    )
    #: Cloud password to manage nodes
    #:
    #: (required for: Openstack)
    cloud_userpassword = Unicode(
        config=True
    )
    #: Cloud tenant or project name where spawns notebook nodes
    #:
    #: (required for: Openstack)
    cloud_project = Unicode(
        config=True
    )
    #: Module where libcloudspawner can find a jinja2 template folder for
    #: userdata script which pass to cloud-init
    userdata_template_module = Unicode(
        'libcloudspawner',
        config=True
    )
    #: Template name for cloud-init userdata script
    userdata_template_name = Unicode(
        'userdata.sh.j2',
        config=True
    )
    #: List of tuple for nodes flavors like
    #:
    #: >>>  [('Simple machine', 's0-small'),
    #: >>>   ('Mouhahaha machine','h4-bigmem')]
    #:
    #: (required for Openstack)
    machine_sizes = List(
        [],
        config=True,
    )
    #: Region where deploy nodes
    #:
    #: (required for Openstack)
    cloud_region = Unicode(
        'RegionOne',
        config=True
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
    #: Network name where connect nodes
    #:
    #: (required for Openstack)
    machine_net = Unicode(
        config=True
    )
    #: Cloud node identifier
    machineid = Unicode(
        ""
    )
    #: NOT IMPLEMENTED (force username on remote machine, instead of auth user)
    #:
    #: ..todo: Used of forceuser inside cloud-init template
    forceuser = Unicode(
        "",
        config=True
    )
    #: Notebook args to pass on nodes
    notebookargs = Unicode(
        "",
        config=True
    )
    #: Libcloud Parameters, see managers documentations for details
    libcloudparams = Dict(
        {},
        config=True,
        help='LibCloud cloud Configuration'
    )
    #: To retrieve some metrics (like spawn time...) via statsd
    #: Statsd dict params host, port and prefix. See StatsClient for more options
    statsdparams = Dict(
        {},
        config=True
        )

    def __init__(self, **kwargs):
        super(LibcloudSpawner, self).__init__(**kwargs)

        # Trying to bind to statsd
        self.statsd = None
        if self.statsdparams:
            try:
                self.statsd = StatsClient(**self.statsdparams)
            except:
                self.log.info('Failed to connect to statsd daemon')

        self.nodemanager = NodeManager(self,
                                       logguer=self.log)

        self.user_options_from_form = None

        if self.user.state:
            self.load_state(self.user.state)
            self.nodemanager.retrieve_node(self.user.state['machineid'])

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
            Load machineid from state
        """
        super(LibcloudSpawner, self).load_state(state)

        if state:
            self.machineid = state.get('machineid')
        pass

    def get_state(self):
        """
            Add machineid to state
        """
        state = super(LibcloudSpawner, self).get_state()
        if self.machineid:
            state['machineid'] = self.machineid
        return state

    @gen.coroutine
    def start(self):
        """
            Start notebook node and poll machine until timeout
        """
        jhub_env = {}
        # Keeping only env related to Jupyter (exclude PATH, LANG...)
        for key, value in self.get_env().items():
            if ("JUPYTER" in key) or ("JPY" in key):
                jhub_env[key]=value

        # Node creation
        self.nodemanager.create_machine(jhub_env,
                                        self.user_options_from_form)

        for i in range(self.start_timeout):
            status = yield self.poll()
            if status is None:
                # Notebook ready
                self.user.server.ip = self.nodemanager.node_ip
                self.user.server.port = self.nodemanager.node_port
                self.machineid = self.nodemanager.node.id
                self.log.info("Yippee notebook ready at %s:%s (%s)" % 
                              (self.user.server.ip,
                               self.user.server.port,
                               self.machineid))
                self.db.commit()
                return(self.user.server.ip, self.user.server.port)
            else:
                yield gen.sleep(1)
        # Timeout start failed...
        self.log.debug("Spawn Timeout, deleting Cloud instance %s ")
        self.nodemanager.destroy_node()
        return None

    @gen.coroutine
    def poll(self):
        """
            Poll the process
        """
        return self.nodemanager.get_node_status()

    @gen.coroutine
    def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        self.nodemanager.destroy_node()
        return
