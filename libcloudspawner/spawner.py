import random, string
import requests
import time
from time import sleep

import socket
import http.client

from tornado import gen

from jupyterhub.spawner import Spawner
from traitlets import (
    Instance, Integer, Unicode, List, Bool
)
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

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

    def wait_notebook(self, server, port, timeout=None):
        """ Wait for notebook running by simply request host:port
            @param timeout: in seconds
            @return: True of False
        """
        try:
            requests.get("http://%s:%s" % (server,
                                            port),
                                            timeout=timeout)
        except requests.exceptions.RequestException as e:
            print(e)
            return None
        return True

    def _options_form_default(self):
        """ These options are set by final user in an HTML form
            Users choices are passed to spawner in self.user_options
        """
        formhtml = []
        formhtml.append("<label for=\"args\"> Virtual machine image </label>")
        formhtml.append("<select name=\"image\">")
        for size in self.machine_images:
            option = "<option value=\"%s\"> %s </option>" % (size[1], size[0])
            formhtml.append(option)
        formhtml.append("</select>")
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

    #def get_libcloud_driver(self):
    #    """
    #        Retrieve LibCloudDriver 
    #    """
    #    cls = get_driver(Provider.OPENSTACK)
    #    driver = cls(self.cloud_user, self.cloud_userpassword,
    #                 ex_force_auth_version='3.x_password',
    #                 ex_force_auth_url=self.cloud_url,
    #                 ex_force_service_region=self.cloud_region,
    #                 ex_tenant_name=self.cloud_project)
    #    return driver

    #def get_machine(self, machineid):
    #    """
    #        Retrieve machine informations
    #    """
    #    self.log.debug("Getting Machine")
    #    driver = self.get_libcloud_driver()
    #    try:
    #        m = driver.ex_get_node_details(machineid)
    #    except:
    #        return None
    #    self.log.debug(m)
    #    return m
    
    #def get_machine_status(self):
    #    machineinfos = self.get_machine(self.machineid)
    #    if machineinfos:
    #        if machineinfos.state == 'running':
    #            # Machine running, trying http
    #            self.log.debug("Machine running. Trying HTTP request on 8000")
    #            try:
    #                httptest = requests.head("http://%s:8000" % machineinfos.private_ips[0], max_retries=1)
    #            except:
    #                httptest = None
    #            self.log.debug(httptest)
    #            return None
    #    return 1

#     def create_machine(self):
#         """
#             Create a machine, return machine informations
#         """
#         self.log.debug("create_machine start")
#         driver = self.get_libcloud_driver()
# 
#         if self.forceuser:
#             username = self.forceuser
#         else:
#             username = self.user.name
# 
#         userdata = """#!/bin/bash
# cat <<EOF > /etc/systemd/system/jupyterhub-singleuser.service
# [Unit]
# Description=JupyterHub-singleuser instance
#  
# [Service]
# User={user}
# Environment=JPY_API_TOKEN={apitoken}
# ExecStart=/usr/local/bin/jupyterhub-singleuser --port=8000 --ip=0.0.0.0 --user={user} --cookie-name={cookiename} --base-url={baseurl} --hub-prefix={hubprefix} --hub-api-url={apiurl}  {notebookargs} \$@
# [Install]
# WantedBy=multi-user.target
# EOF
# 
# cat <<EOF > /etc/systemd/system/register-conda-on-jupyter.service
# [Unit]
# Description=Register Conda on Jupyter
# After=jupyterhub-singleuser.service
#  
# [Service]
# Type=oneshot
# User={user}
# ExecStart=/bin/bash --login /tmp/register-conda-on-jupyter.sh
# StandardOutput=journal+console
# EOF
# 
# cat <<EOF > /tmp/register-conda-on-jupyter.sh
# #!/bin/bash
# 
# if which conda >/dev/null; then
#         condaenvs="\$(conda info --env |grep -v \# |grep -v ^$ |cut -f1 -d " ")"
# 
#         for c in \$condaenvs
#         do
#                 echo "Trying to register Conda env \$c"
#                 source activate \$c
#                 python -m ipykernel install --user --name \$c --display-name "Python (conda-\$c)"
#         done
# else
#     echo "Conda not found"
# fi
# exit 0
# EOF
# 
# 
# systemctl daemon-reload
# systemctl enable register-conda-on-jupyter.service
# systemctl restart jupyterhub-singleuser.service
# systemctl enable jupyterhub-singleuser.service
# systemctl start register-conda-on-jupyter.service
# 
# 
# 
# sudo -u {user} bash /tmp/register-conda-on-jupyter.sh
# 
# """.format(
#                    apitoken=self.get_env()["JPY_API_TOKEN"],
#                    user=username,
#                    cookiename=self.user.server.cookie_name,
#                    baseurl=self.user.server.base_url,
#                    hubprefix=self.hub.server.base_url,
#                    apiurl=self.hub.api_url,
#                    notebookargs=self.notebookargs,
#             )
# 
#         images = driver.list_images()
#         sizes = driver.list_sizes()
#         nets = driver.ex_list_networks()
# 
#         for i in images:
#             if i.name == self.user_options['machineimage']:
#                 self.log.debug("Image found %s" % i.name)
#                 machineimage = i
#         for s in sizes:
#             if s.name == self.user_options['machinesize']:
#                 self.log.debug("Size found %s" % s.name)
#                 machinesize = s
#         for n in nets:
#             self.log.debug(n.name)
#             if n.name == self.machine_net:
#                 self.log.debug("Network found %s" % n.name)
#                 machinenet = n
# 
#         randomstring = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
# 
#         machinename = ("jpy-%s-%s" % (self.user.name, randomstring))
#         node = driver.create_node(name=machinename,
#                                   image=machineimage,
#                                   size=machinesize,
#                                   networks=[machinenet],
#                                   ex_keyname="tristanlt",
#                                   ex_userdata=userdata)
# 
#         self.log.debug("CreateMachine waiting while node is running (or timeout)")
#         nodesok = driver.wait_until_running([node],
#                                           wait_period=1,
#                                           timeout=60)
# 
#         #import pdb
#         #pdb.set_trace()
# 
#         if nodesok:
#             self.log.debug("CreateMachine node is running, checking user notebook")
#             nodeok = nodesok[0][0]
# 
#             self.log.debug("CreateMachine checking notebook at %s:%s" % ([nodeok.public_ips or nodeok.private_ips][0][0], str(8000)))
#             notebookcheck = self.wait_notebook([nodeok.public_ips or nodeok.private_ips][0][0],
#                                                8000,
#                                                60)
#             if notebookcheck:
#                 self.log.debug("CreateMachine notebook responding :)")
#                 return nodeok
#             else:
#                 return None
#         else:
#             self.log.debug("CreateMachine node  not running after timeout")
#             return None

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
        machine = self.create_machine()
        if machine:
            self.log.debug("START receive node info")
            # Nice ! our instance is up and ready !
            #Setting port
            self.user.server.port = 8000

            #Setting IP, public IP or private 
            if len(machine.private_ips) > 0:
                self.user.server.ip = machine.private_ips[0]
            if len(machine.public_ips) > 0:
                self.user.server.ip = machine.public_ips[0]

            self.machineid = machine.id
            self.db.commit()
        else:
            self.log.debug("START create_machine return no machine :(")
            return None
        return(self.user.server.ip, self.user.server.port)


    @gen.coroutine
    def poll(self):
        """Poll the process"""
        if self.machineid:
            return self.get_machine_status()
        else:
            return 1

    @gen.coroutine
    def stop(self):
        self.log.debug("DELETE Cloud instance %s " % self.machineid)
        driver = self.get_libcloud_driver()
        if not self.get_machine_status():
            self.log.debug("Cloud instance running, send delete for %s " % self.machineid)
            m = self.get_machine(self.machineid)
            driver.destroy_node(m)
        return
