# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Vapor Driver

@note: This driver is base on libcloud Dummy driver
"""
import uuid
import socket
import struct
import time

from libcloud.common.base import ConnectionKey
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver
from libcloud.compute.types import Provider, NodeState
from libcloud.common.types import LibcloudError

class VaporConnection(ConnectionKey):
    """
    Vapor connection class (for test purpose only)
    """

    def connect(self, **kwargs):
        pass


class VaporNodeDriver(NodeDriver):
    """
    Vapor node driver (for test purpose only)

    """

    name = "Vapor Node Provider"
    website = 'https://github.com/tristanlt/jupyter-libcloudspawner'
    #type = Provider.VAPOR

    def __init__(self, **kwargs):
        """
        This init create one fixture node
        """

        self._images = {}
        self._images['u16-jhub-usernotebook'] = NodeImage(id=1, 
                                                          name="u16-jhub-usernotebook",
                                                          driver=self)
        self._images['deb8-jhub-usernotebook'] = NodeImage(id=2,
                                                           name="deb8-jhub-usernotebook",
                                                           driver=self)
        self._sizes = {}
        self._sizes['n0-small'] = NodeSize(id=1,
                     name="n0-small",
                     ram=128,
                     disk=4,
                     bandwidth=500,
                     price=4,
                     driver=self)
        self._sizes['n0-medium'] = NodeSize(id=2,
                     name="n0-medium",
                     ram=512,
                     disk=16,
                     bandwidth=1500,
                     price=8,
                     driver=self),

        self._networks = {}
        self._networks['provider-network'] = {'name': 'provider-network'}
        self._networks['project-network'] = {'name': 'project-network'}

        # Node List
        self.nl = []
        self.nl.append(Node(id=1,
                            name='dummy-%d' % (1),
                            state=NodeState.RUNNING,
                            public_ips=['172.16.42.1'],
                            private_ips=[],
                            driver=self,
                            size=self._sizes['n0-small'],
                            image=self._images['deb8-jhub-usernotebook'])
                       )

        self.connection = VaporConnection(kwargs)


    def get_uuid(self):
        """
        Return an UUID identifier
        """
        return str(uuid.uuid4())

    def list_nodes(self):
        """
        List Vapor nodes
        """
        return self.nl

    def destroy_node(self, node):
        """
        Destroy fake node
        """

        node.state = NodeState.TERMINATED
        self.nl.remove(node)
        return True

    def list_images(self, location=None):
        """
        Returns a list of images as a cloud provider might have
        """
        return [v for k,v in self._images.items()]

    def list_sizes(self):
        """
        Returns a list of node sizes as a cloud provider might have
        """

        return [v for k,v in self._sizes.items()]

    def ex_list_networks(self):
        """
        Get project network list
        """

        return [v for k,v in self._networks.items()]

    def create_node(self, name=None,
                    image=None,
                    size=None,
                    networks=[],
                    ex_userdata=None):
        """
        Creates a dummy node; the node id is equal to the number of
        nodes in the node list

        @inherits: :class:`NodeDriver.create_node`
        """
        newnodeid = len(self.nl) + 1
        n = Node(id=newnodeid,
                 name=name,
                 state=NodeState.PENDING,
                 public_ips=['172.16.42.%s' % str(newnodeid)],
                 private_ips=[],
                 driver=self,
                 size=size,
                 image=image)
        self.nl.append(n)
        return n

    def wait_until_running(self, nodes=[],
                           wait_period=1,
                           timeout=60):

        # This fake method only process first item 
        node = nodes[0]

        if node.name == 'too_slow_or_buggy_node':
            raise LibcloudError(value="Raise timeout", driver=self)

        if node.name == 'slow_node':
            time.sleep(int(timeout/2))
            node.state = NodeState.RUNNING

        if node.name == 'fast_node':
            node.state = NodeState.RUNNING

        return [(node, node.public_ips)]

    def ex_get_node_details(self, node_id):
        for n in self.nl:
            if n.id == node_id:
                return n
        return None


def _ip_to_int(ip):
    return socket.htonl(struct.unpack('I', socket.inet_aton(ip))[0])


def _int_to_ip(ip):
    return socket.inet_ntoa(struct.pack('I', socket.ntohl(ip)))

if __name__ == "__main__":
    import doctest

    doctest.testmod()
