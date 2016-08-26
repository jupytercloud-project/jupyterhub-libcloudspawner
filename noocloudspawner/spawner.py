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

import requests
import time
from time import sleep

class NooCloudSpawner(Spawner):
    """A Spawner that instanciate notebook inside NooCloud."""

    nooapi_url = Unicode(
        config=True,
        help=''
    )
    nooapi_user = Unicode(
        config=True,
        help=''
    )
    nooapi_userpassword = Unicode(
        config=True,
        help=''
    )
    nooapi_project = Unicode(
        config=True,
        help=''
    )
    nooapi_profil = Unicode(
        config=True,
        help=''
    )
    machineid = Integer(
        0,
        help=''
    )

    def readConf(self):
        conf={}
        conf['confnooapiurl'] = self.nooapi_url
        conf['confusername'] = self.nooapi_user
        conf['confpassword'] = self.nooapi_userpassword
        return conf

    def readCloudInfo(self):
        cloudinfo={}
        cloudinfo['cloudname'] = "NooCloud"
        cloudinfo['domainname'] = "default"
        cloudinfo['authurl'] = "https://noocloud.univ-brest.fr/keystone/v3"
        cloudinfo['dashboard'] = "https://noocloud.univ-brest.fr/horizon/"
        cloudinfo['regionname'] = "RegionOne"
        return cloudinfo
    
    def getToken(self):
        """
            Authenticate on Keystone, retrieve an unscopped token 
        """
        conf = self.readConf()
        cloudinfo = self.readCloudInfo()
    
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(auth_url=cloudinfo['authurl'],
                                        username=conf['confusername'],
                                        password=conf['confpassword'],
                                        user_domain_name=cloudinfo['domainname'],)
        sess = session.Session(auth=auth)
        try:
            token = sess.get_token()
        except:
            token = None
        self.log.debug(token)
        return token

    def getMachine(self, machineid):
        """
            Retrieve machine informations
        """
        conf = self.readConf()
        token = self.getToken()
        headers = {'X-Auth-Token': token}

        url = conf['confnooapiurl']+"/machines/"+str(machineid)

        try:
            machineinfos = requests.get(url, headers=headers).json()
            self.log.debug(machineinfos)
            return machineinfos
        except:
            return None
    
    def getMachineStatus(self):
        self.log.debug("Getting Machine status")
        machineinfos = self.getMachine(self.machineid)
        self.log.debug(machineinfos)
        if machineinfos:
            if machineinfos['status'] == 'ACTIVE':
                return None
        return 1

    def createMachine(self):
        """
            Create a machine, return machine informations
        """
        conf = self.readConf()
        token = self.getToken()
        headers = {'X-Auth-Token': token}

        projecturl = conf['confnooapiurl']+"/projects/"+self.nooapi_project+"/"
        profilurl = conf['confnooapiurl']+"/profils/"+self.nooapi_profil+"/"
        payload = {'name': "jupytermachine", 'project': projecturl, 'profile': profilurl}

        url = conf['confnooapiurl']+"/machines/"
        try:
            r = requests.post(url, data=payload, headers=headers).json()
        except:
            return None
        return r

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
        self.machineid = 0

    @gen.coroutine
    def start(self):
        """Start the process"""
        self.log.debug("DEBUG start nooSpwaner")
        
        machine = self.createMachine()
        
        timeout_start = time.time()
        timeout = 30  # seconds
        
        cont = True
        
        while (time.time() < timeout_start + timeout) and cont:
            m = self.getMachine(machineid=machine["id"])
            if m['status'] == "ACTIVE":
                # Nice ! our instance is up and ready !
                self.user.server.port = 8000
                self.user.server.ip = m['ipaddr']
                self.machineid = m['id']
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
    def stop(self, now=False):
        """stop the subprocess

        if `now`, skip waiting for clean shutdown
        """
        return
        #if not now:
        #    status = yield self.poll()
        #    if status is not None:
        #        return
        #    self.log.debug("Interrupting %i", self.pid)
        #    yield self._signal(signal.SIGINT)
        #    yield self.wait_for_death(self.INTERRUPT_TIMEOUT)

        ## clean shutdown failed, use TERM
        #status = yield self.poll()
        #if status is not None:
        #    return
        #self.log.debug("Terminating %i", self.pid)
        #yield self._signal(signal.SIGTERM)
        #yield self.wait_for_death(self.TERM_TIMEOUT)

        ## TERM failed, use KILL
        #status = yield self.poll()
        #if status is not None:
        #    return
        #self.log.debug("Killing %i", self.pid)
        #yield self._signal(signal.SIGKILL)
        #yield self.wait_for_death(self.KILL_TIMEOUT)

        #status = yield self.poll()
        #if status is None:
        #    # it all failed, zombie process
        #    self.log.warn("Process %i never died", self.pid)
