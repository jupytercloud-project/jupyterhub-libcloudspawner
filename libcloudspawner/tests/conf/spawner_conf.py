from bunch import Bunch

def spawner_conf_ok():
	spawner_conf = Bunch()
	spawner_conf.cloud_user = 'user'
	spawner_conf.cloud_userpassword = 'secret'
	spawner_conf.cloud_url = 'https://api.noo.cloud/keystone/v3/auth/tokens'
	spawner_conf.cloud_region = 'region'
	spawner_conf.cloud_project = 'cloudproject'
	spawner_conf.machine_sizes = [("n0-small", "n0-small"), ("n0-medium", "n0-medium")]
	spawner_conf.machine_images = [("Default image","u16-jhub-usernotebook")]
	spawner_conf.cloud_url = 'https://api.noo.cloud/keystone/v3/auth/tokens'
	spawner_conf.notebookargs = '--notebook-dir=~'
	spawner_conf.machine_net = "project-network"
	spawner_conf.forceuser = ""
	# Hub configuration
	spawner_conf.hub = Bunch()
	spawner_conf.hub.server = Bunch()
	spawner_conf.hub.api_url = "http://jupyterhub/api"
	spawner_conf.hub.server.base_url = "/app/notebooks"
	spawner_conf.user = Bunch()
	spawner_conf.user.name = "rickdangerous"
	spawner_conf.user.server = Bunch()
	spawner_conf.user.server.cookie_name = 'JPY_RICKDANGEROUS_COOKIE'
	spawner_conf.user.server.base_url = '/app/notebooks'
	# Fake data from HTML User Form
	spawner_conf.user_options = Bunch()
	spawner_conf.user_options.machineimage = 'u16-jhub-usernotebook'
	spawner_conf.user_options.machinesize = 'n0-small'
	return spawner_conf