import random
import string
import requests

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


class NodeManager:
    """ NodeManager have tools to connect with cloud,
    NodeManager create, audit and delete virtual machines
    """

    def __init__(self, spawner_conf):

        cls = get_driver(Provider.OPENSTACK)
        self.driver = cls(spawner_conf.cloud_user, spawner_conf.cloud_userpassword,
                     ex_force_auth_version='3.x_password',
                     ex_force_auth_url=spawner_conf.cloud_url,
                     ex_force_service_region=spawner_conf.cloud_region,
                     ex_tenant_name=spawner_conf.cloud_project)

        self.node = None
        self.node_ip = None
        self.node_port = None

    def _update_node_cloudstate(self):
        """
        Update nodes status
        """
        try:
            self.node = self.driver.ex_get_node_details(self.node.id)
        except:
            self.log.debug("Can not retrieve node information from cloud provider")

    def _update_node_net_informations(self):
        """
        Get first public_ips or the first private_ips
        """
        node = self.get_machine()
        if ([node.public_ips or node.private_ips]):
            self.node_ip = [node.public_ips or node.private_ips][0]
        else:
            self.node_ip = None

    def _check_notebook(self, timeout=None):
        """ Wait for notebook running by simply request host:port
            @param timeout: in seconds
            @return: True of False
        """
        try:
            requests.get("http://%s:%s" % (self.node_ip, self.node_port),
                         timeout=timeout)
        except requests.exceptions.RequestException as e:
            print(e)
            return None
        return True

    def get_node(self):
        """
        Return node after updating node informations from cloud provider
        @return node or None
        """
        self._update_node_cloudstate()
        return self.node

    def get_machine_status(self):
        """
        Check that node and notebook are OK 
        @return None if ok, 1 else
        """
        node = self.get_machine()
        if node:
            if node.state == 'running':
                # Node Ok, updating network informations
                self._update_node_net_informations()

                # Notebook ? Did you respond ?
                if self._check_notebook(self, timeout=60):
                    return None
                else:
                    return 1
        return 1

    def create_machine(self):
        """
            Create a machine, return machine informations
        """
        self.log.debug("create_machine start")

        if self.spawner_conf.forceuser:
            username = self.spawner_conf.forceuser
        else:
            username = self.spawner_conf.user.name

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

cat <<EOF > /etc/systemd/system/register-conda-on-jupyter.service
[Unit]
Description=Register Conda on Jupyter
After=jupyterhub-singleuser.service
 
[Service]
Type=oneshot
User={user}
ExecStart=/bin/bash --login /tmp/register-conda-on-jupyter.sh
StandardOutput=journal+console
EOF

cat <<EOF > /tmp/register-conda-on-jupyter.sh
#!/bin/bash

if which conda >/dev/null; then
        condaenvs="\$(conda info --env |grep -v \# |grep -v ^$ |cut -f1 -d " ")"

        for c in \$condaenvs
        do
                echo "Trying to register Conda env \$c"
                source activate \$c
                python -m ipykernel install --user --name \$c --display-name "Python (conda-\$c)"
        done
else
    echo "Conda not found"
fi
exit 0
EOF


systemctl daemon-reload
systemctl enable register-conda-on-jupyter.service
systemctl restart jupyterhub-singleuser.service
systemctl enable jupyterhub-singleuser.service
systemctl start register-conda-on-jupyter.service



sudo -u {user} bash /tmp/register-conda-on-jupyter.sh

""".format(
                   apitoken=self.get_env()["JPY_API_TOKEN"],
                   user=username,
                   cookiename=self.user.server.cookie_name,
                   baseurl=self.user.server.base_url,
                   hubprefix=self.hub.server.base_url,
                   apiurl=self.hub.api_url,
                   notebookargs=self.notebookargs,
            )

        images = self.driver.list_images()
        sizes = self.driver.list_sizes()
        nets = self.driver.ex_list_networks()

        for i in images:
            if i.name == self.spawner_conf.user_options['machineimage']:
                self.log.debug("Image found %s" % i.name)
                machineimage = i
        for s in sizes:
            if s.name == self.spawner_conf.user_options['machinesize']:
                self.log.debug("Size found %s" % s.name)
                machinesize = s
        for n in nets:
            self.log.debug(n.name)
            if n.name == self.spawner_conf.machine_net:
                self.log.debug("Network found %s" % n.name)
                machinenet = n

        randomstring = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))

        machinename = ("jpy-%s-%s" % (self.spawner_conf.user.name, randomstring))
        node = self.driver.create_node(name=machinename,
                                  image=machineimage,
                                  size=machinesize,
                                  networks=[machinenet],
                                  ex_keyname="tristanlt",
                                  ex_userdata=userdata)

        self.log.debug("CreateMachine waiting while node is running (or timeout)")
        nodesok = self.driver.wait_until_running([node],
                                          wait_period=1,
                                          timeout=60)

        if nodesok:
            self.log.debug("CreateMachine node is running, checking user notebook")
            self.node = nodesok[0][0]
            
            self._update_node_net_informations()
            
            if self.w_check_notebook(timeout=60):
                return True
            else:
                return False
        else:
            self.log.debug("CreateMachine node not running after timeout")
            return False