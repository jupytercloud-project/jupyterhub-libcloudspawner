About LibCloudSpawner
=====================

LibcloudSpawner is a JupyterHub Spawner, it allow JupyterHub to deploy users notebooks inside cloud instance. One instance, one user. 

LibcloudSpawner is based on Apache Libcloud, Apache LibCloud provide an abstraction API for a lot of cloud provider. By the way, LibcloudSpawner will support OpenStack, Google Cloud Engine, Amazone AWS or CloudStack...

.. note::
	For the moment, OpenStack is the only supported cloud provider. More cloud provider coming soon...



.. image:: _static/general-usage.png
   :width: 600px
   :alt: LibcloudSpawner usage 
   :align: center
   
Internal
--------

.. image:: _static/flow-diagram.png
   :width: 600px
   :alt: Flow Diagram
   :align: center