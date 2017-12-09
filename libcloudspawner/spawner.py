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

from libcloudspawner.manager.nodemanager import NodeManager
from statsd import StatsClient


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
    userdata_template_module = Unicode(
        'libcloudspawner',
        config=True,
        help='''Module where libcloudspawner can find a jinja2 template folder for 
        userdata script
        '''
    )
    userdata_template_name = Unicode(
        'userdata.sh.j2',
        config=True,
        help='''Template name for userdata script'''
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
    machine_images = List(
        [],
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
    libcloudparams = Dict(
        {},
        config=True,
        help='LibCloud cloud Configuration'
    ) 
    statsdparams = Dict(
        {},
        config=True,
        help='Statsd dict params host, port and prefix. See StatsClient for more options.'
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
        if self.user.state:
            self.load_state(self.user.state)
            self.nodemanager.retrieve_node(self.user.state['machineid'])

    def _options_form_default(self):
        """ These options are set by final user in an HTML form
            Users choices are passed to spawner in self.user_options
        """
        formhtml = []
        formhtml.append("<label for=\"args\"> Notebook type </label>")
        formhtml.append("<select name=\"image\">")
        for size in self.machine_images:
            option = "<option value=\"%s\"> %s </option>" % (size[1], size[0])
            formhtml.append(option)
        formhtml.append("</select>")
        formhtml.append("<label for=\"args\"> Ressources </label>")
        formhtml.append("<select name=\"size\">")
        for size in self.machine_sizes:
            option = "<option value=\"%s\"> %s </option>" % (size[1], size[0])
            formhtml.append(option)
        formhtml.append("</select>")
        return(" ".join(formhtml))

    def options_from_form(self, formdata):
        options = {}
        options['machinesize'] = ""
        options['machineimage'] = ""

        machineimage = formdata.get('image', "")[0]
        machinesize = formdata.get('size', "")[0]
        options['machineimage'] = machineimage
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

    def load_state(self, state):
        """load machineid from state"""
        super(LibcloudSpawner, self).load_state(state)
        self.machineid=state.get('machineid')
        pass

    def get_state(self):
        """add machineid to state"""
        state = super(LibcloudSpawner, self).get_state()
        if self.machineid:
            state['machineid'] = self.machineid
        return state

    @gen.coroutine
    def start(self):
        """Start the process"""

        self.log.debug(self.get_env()["JPY_API_TOKEN"])

        api_token = self.get_env()["JPY_API_TOKEN"]
        return self.nodemanager.create_machine(api_token)

#         if res:
#             # Nice ! our instance is up and ready !
#             self.log.debug("START receive node info")
# 
#             #Setting port
#             self.user.server.ip = self.nodemanager.node_ip
#             self.user.server.port = self.nodemanager.node_port
#             self.machineid = self.nodemanager.node.id
#             self.log.info("Notebook ready at %s:%s (%s)" %
#                           (self.user.server.ip,
#                            self.user.server.port,
#                            self.machineid))
#             self.db.commit()
#             yield (self.user.server.ip, self.user.server.port)
#         else:
#             self.log.debug("START create_machine return no machine :(")
#             yield None


    @gen.coroutine
    def poll(self):
        """Poll the process"""
        return self.nodemanager.get_node_status()

    @gen.coroutine
    def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        self.nodemanager.destroy_node()
        return
