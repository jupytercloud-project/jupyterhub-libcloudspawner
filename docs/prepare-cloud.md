# Prepare Cloud

In this section, we're going to talk about preparing cloud project to install comfortably Jupyterhub and his userserver's instances.

You'll need

* a cloud project
* cloud credentials for jupyterhub
* a project network & routing
* [security groups & rules](#security-groups-and-rules)
* [one instance for JupyterHub service](#jupyterhub-instance)
* one floating-ip for JupyterHub service
* one or more [templates for userserver's instances](#images-for-userservers-instance)
* one or more [flavors for userserver's instances](#flavors-for-userservers-instance)

## Cloud credentials and URL for Jupyterhub

LibcloudSpawner will connect on cloud APIs in order to manage userserver life-cycle. It will need cloud credentials.

You can use your login and password.This is rarely a good idea.


!!! example "Create Application Credentials"

    === "OpenStack (Horizon)"

        Go to OpenStack Horizon dashboard and connect yourself.

        * Go to section **Indentity** > **Application Credentials**
        * Press **Create Application Credentials**
        * Fill form with (at least):
            * **Name** (mandatory)
            * **Expiration Date**
            * **Roles** : `member`

        Press **Create Application Credential** then make a note of the `id` and `secret`, and download `clouds.yaml`.

        Open `clouds.yaml` and make a note of the identity `auth_url` and `region_name`.

    === "OpenStack (cli)"
        
        ```
        openstack application credential create --description "Jupyterhub libcloudSpawner" \
            --role member \
            --restricted \
            jupyterhub-credentials
        ```
        Make a note of the `id` and `secret`

        Get identity URL for your cloud.
        ```
        openstack endpoint list --service identity --interface public -c URL
        ```
        Make a note of the identity `URL`


## Security groups and rules

!!! warning

    You can either create a single security group and authorize everything, or restrict access for each group.

    For example, it is sometimes necessary to prohibit traffic between user servers.

For **jupyterhub-secgroup**, applied to jupyterhub instances, authorize at least

* allow http(80) and https(443) from outside
* allow ssh(22) and 443 from outside
* allow 8000, 8001 and 8080 from **userserver-secgroup**
* allow all tcp, udp from inside to outside

For **userserver-secgroup**, applied to userserver instances, authorize at least

* allow 8000-8999 from **jupyterhub-secgroup**
* allow all tcp, udp from inside to outside

## Jupyterhub instance

Jupyterhub will just have to manage userservers and support trafic.

Requirements :

* Linux operating system
* vCPUS min : 2 vcpus
* memory min : 2Gb
* storage : few Gb only

!!! note "Floating IP"

    In order to access your service, you should associate a floating-ip to your JupyterHub. Jupyterhub embeds a service called configurable-http-proxy that is placed in front of userservers, so all communication passes through jupyterhub.

## Images for userserver's instance

When libcloudspawner will start a userserver, it will use an image. At instance creation, libcloudspawner will provide [cloud-init](https://cloud-init.io) user-data that install missing dependencies and configure the systemd service that launches Jupyter jupyterhub-singleuser.

If want to use the default user-data template (`userdata.sh.j2`), you're image must comply with these requirements :

* cloud-init capability
* systemd
* jupyterhub-singleuser is available somewhere system `PATH`

!!! example "Create compatible images"

    === "Ubuntu 22.04"

        1. Start an instance with an Ubuntu 22.04 base image offered by your cloud provider

        2. Connect yourself with ubuntu user and install dependencies.

        ```
        sudo apt update
        sudo apt upgrade
        sudo apt install node-configurable-http-proxy
        sudo apt install python3-pip
        sudo pip install jupyterlab
        sudo pip install jupyterhub==4.0.2
        sudo pip install pandas==2.2.0
        ```
        3. Create a snapshot of this instance `ubuntu-22.04-jupyterhub`


??? question "Use system packages, conda/mamba or apptainer ?"

    In this example, in order to keep things simple, we use system packages.

    We could also have installed an environment with micromamba and added this environment to the system path. See [custom section](./custom/images.md) for other ideas.


## Flavors for userserver's instance

Identify and note the flavors you wish to make available to users.

!!! warning "Make sure the template is large enough for the image"

    Make sure the template is large enough for the image.

    * disk size
    * recommended memory
    * recommended CPUs