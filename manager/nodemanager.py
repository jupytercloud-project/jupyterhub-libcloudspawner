import random
import string
#import requests
import socket

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


class NodeManager:
    """ NodeManager have tools to connect with cloud,
    NodeManager create, audit and delete virtual machines
    """

    def __init__(self, spawner_conf, logguer):

        cls = get_driver(Provider.OPENSTACK)
        self.driver = cls(spawner_conf.cloud_user, spawner_conf.cloud_userpassword,
                     ex_force_auth_version='3.x_password',
                     ex_force_auth_url=spawner_conf.cloud_url,
                     ex_force_service_region=spawner_conf.cloud_region,
                     ex_tenant_name=spawner_conf.cloud_project)

        self.logguer = logguer
        self.spawner_conf = spawner_conf
        self.node = None
        self.node_ip = None
        self.node_port = 8000 # TODO this parameter should be set by spawner_conf
        self.timeout = 90 # TODO this parameter should be set by spawner_conf 

    def _update_node_cloudstate(self):
        """
        Update nodes status
        """
        try:
            self.node = self.driver.ex_get_node_details(self.node.id)
        except:
            self.logguer.debug("Can not retrieve node information from cloud provider")

    def _update_node_net_informations(self):
        """
        Get first public_ips or the first private_ips
        """
        node = self.get_node()
        if ([node.public_ips or node.private_ips]):
            self.node_ip = [node.public_ips or node.private_ips][0][0]
        else:
            self.node_ip = None

    def _check_notebook(self):
        """ Wait for notebook running by simply request host:port
            @param timeout: in seconds
            @return: True of False
        """
        self.logguer.debug("HTTP Notebook check @%s:%s" % (self.node_ip, self.node_port))

        try:
            conn = socket.create_connection((self.node_ip, self.node_port), timeout=self.timeout)
            #requests.get(notebook_url,
            #             timeout=self.timeout)
        except:
            #except requests.exceptions.RequestException as e:
            #print(e)
            return None
        self.logguer.debug("HTTP Notebook check @%s:%s is OK" % (self.node_ip, self.node_port))
        return True

    def get_node(self):
        """
        Return node after updating node informations from cloud provider
        @return node or None
        """
        self._update_node_cloudstate()
        return self.node

    def destroy_node(self):
        """
        Destroy node
        @return node or None
        """
        try:
            self.driver.destroy_node(self.node)
        except:
            print('Node destroy failed')

    def get_node_status(self):
        """
        Check that node and notebook are OK 
        @return None if ok, 1 else
        """
        node = self.get_node()
        if node:
            if node.state == 'running':
                # Node Ok, updating network informations
                self._update_node_net_informations()

                # Notebook ? Did you respond ?
                if self._check_notebook():
                    return None
                else:
                    return 1
        return 1

    def create_machine(self, api_token):
        """
            Create a machine, return machine informations
        """
        self.logguer.debug("create_machine start")

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
                   apitoken=str(api_token),
                   user=username,
                   cookiename=self.spawner_conf.user.server.cookie_name,
                   baseurl=self.spawner_conf.user.server.base_url,
                   hubprefix=self.spawner_conf.hub.server.base_url,
                   apiurl=self.spawner_conf.hub.api_url,
                   notebookargs=self.spawner_conf.notebookargs,
            )

        images = self.driver.list_images()
        sizes = self.driver.list_sizes()
        nets = self.driver.ex_list_networks()

        for i in images:
            if i.name == self.spawner_conf.user_options['machineimage']:
                self.logguer.debug("Image found %s" % i.name)
                machineimage = i
        for s in sizes:
            if s.name == self.spawner_conf.user_options['machinesize']:
                self.logguer.debug("Size found %s" % s.name)
                machinesize = s
        for n in nets:
            self.logguer.debug(n.name)
            if n.name == self.spawner_conf.machine_net:
                self.logguer.debug("Network found %s" % n.name)
                machinenet = n

        randomstring = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))

        machinename = ("jpy-%s-%s" % (self.spawner_conf.user.name, randomstring))
        node = self.driver.create_node(name=machinename,
                                  image=machineimage,
                                  size=machinesize,
                                  networks=[machinenet],
                                  ex_keyname="tristanlt",
                                  ex_userdata=userdata)

        self.logguer.debug("CreateMachine waiting while node is running (or timeout)")
        nodesok = self.driver.wait_until_running([node],
                                          wait_period=1,
                                          timeout=self.timeout)

        if nodesok:
            self.logguer.debug("CreateMachine node is running, checking user notebook")
            self.node = nodesok[0][0]

            self._update_node_net_informations()

            if self._check_notebook():
                return True
            else:
                return False
        else:
            self.logguer.debug("CreateMachine node not running after timeout")
            return False