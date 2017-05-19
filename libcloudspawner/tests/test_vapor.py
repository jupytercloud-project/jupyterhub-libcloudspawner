import unittest
from libcloudspawner.tests.libcloud.vapor import VaporNodeDriver
from libcloudspawner.manager.nodemanager import NodeManager

import logging

from libcloudspawner.tests.conf import spawner_conf
from libcloud.common.types import LibcloudError
from libcloud.compute.types import NodeState

class VaporProviderTest(unittest.TestCase):
    """ Test Libcloud Vapor Provider tests
    """

    ### Override nodemanager.NodeManger._get_provider
    # Load Vapor Provider
    def get_vapor_provider(self):
        return VaporNodeDriver

    NodeManager._get_provider = get_vapor_provider

    def test_always_happy(self):
        assert True

    def test_vapor_init_images(self):
        vapor = VaporNodeDriver()
        assert len(vapor._images) == 2

    def test_vapor_init_sizes(self):
        vapor = VaporNodeDriver()
        assert len(vapor._sizes) == 2

    def test_vapor_init_nodes(self):
        vapor = VaporNodeDriver()
        assert len(vapor.nl) == 1

    def test_vapor_init_networks(self):
        vapor = VaporNodeDriver()
        assert len(vapor._networks) == 2

    def test_vapor_list_nodes(self):
        vapor = VaporNodeDriver()
        assert len(vapor.list_nodes()) == 1

    def test_vapor_list_images(self):
        vapor = VaporNodeDriver()
        assert len(vapor.list_images()) == 2

    def test_vapor_list_sizes(self):
        vapor = VaporNodeDriver()
        assert len(vapor.list_sizes()) == 2

    def test_vapor_ex_list_networks(self):
        vapor = VaporNodeDriver()
        assert len(vapor.ex_list_networks()) == 2

    def test_vapor_destroy_node(self):
        vapor = VaporNodeDriver()
        node = vapor.list_nodes()[0]
        vapor.destroy_node(node)
        assert len(vapor.list_nodes()) == 0

    def test_vapor_create_node(self):
        vapor = VaporNodeDriver()
        node = vapor.create_node(name='test',
                          image=vapor.list_images()[0],
                          size=vapor.list_sizes()[0],
                          networks=vapor.ex_list_networks()[0])
        assert node.name == 'test'

    def test_vapor_new_nodes_are_pending(self):
        vapor = VaporNodeDriver()
        node = vapor.create_node(name='fast_node',
                                 image=vapor.list_images()[0],
                                 size=vapor.list_sizes()[0],
                                 networks=vapor.ex_list_networks()[0])
        self.assertEqual(node.state, NodeState.PENDING)

    def test_vapor_wait_nodes_too_slow(self):
        vapor = VaporNodeDriver()
        node = vapor.create_node(name='too_slow_or_buggy_node',
                                 image=vapor.list_images()[0],
                                 size=vapor.list_sizes()[0],
                                 networks=vapor.ex_list_networks()[0])

        self.assertRaises(LibcloudError,
                          vapor.wait_until_running,
                          nodes=[node],
                          wait_period=1,
                          timeout=60)

    def test_vapor_wait_slow_node(self):
        vapor = VaporNodeDriver()
        node = vapor.create_node(name='slow_node',
                                 image=vapor.list_images()[0],
                                 size=vapor.list_sizes()[0],
                                 networks=vapor.ex_list_networks()[0])
        vapor.wait_until_running([node], wait_period=1, timeout=10)
        self.assertEqual(node.state, NodeState.RUNNING)

    def test_vapor_wait_fast_node(self):
        vapor = VaporNodeDriver()
        node = vapor.create_node(name='fast_node',
                                 image=vapor.list_images()[0],
                                 size=vapor.list_sizes()[0],
                                 networks=vapor.ex_list_networks()[0])
        vapor.wait_until_running([node], wait_period=1, timeout=10)
        self.assertEqual(node.state, NodeState.RUNNING)

    def test_vapor_driver_is_vapor(self):
        conf = spawner_conf.spawner_conf_ok()
        log = logging.getLogger()
        manager = NodeManager(conf, log)._get_provider()
        assert manager == VaporNodeDriver


if __name__ == '__main__':
    unittest.main()