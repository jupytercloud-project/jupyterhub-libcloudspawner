c = get_config()
import logging
c.JupyterHub.log_level = logging.DEBUG
c.JupyterHub.base_url = '/app/notebooks'
c.JupyterHub.hub_port = 8081
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.proxy_api_ip = '0.0.0.0'
c.JupyterHub.spawner_class = 'libcloudspawner.spawner.libcloudSpawner'
c.JupyterHub.hub_ip = '0.0.0.0'


c.Spawner.args = ['']

c.LibcloudSpawner.userserver_sizes = [("Small (2 core, 4Gb)", "noocompute.2c.4g"), ("Medium (4 core, 8Gb)", "noocompute.4c.8g")]
c.LibcloudSpawner.userserver_images = [("Ubuntu vanilla 22.04", "ubuntu-jupyterhub-2.3.0") ]
c.LibcloudSpawner.userserver_net = "cloud-ext"
#c.LibcloudSpawner.userserver_keyname = "sysadmin"

c.LibcloudSpawner.userdata_template_name = "userdata.sh.j2"
c.LibcloudSpawner.libcloud_driver_params = {"arg_user_id": "cloud-user-name",
                                    "arg_key": "password",
                                    "ex_force_auth_version": "3.x_password",
                                    "ex_force_auth_url": "https://keystone.cloud.fdqn:5000",
                                    "ex_force_service_region": "universe",
                                    "ex_tenant_name": "my-cloud-project",
                                    "ex_domain_name": "Default",
                                    "verify_ssl_cert": True}
