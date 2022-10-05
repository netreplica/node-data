import os

from flask import Flask, escape, request

def create_app(config=None):
  # create and configure the app
  app = Flask(__name__, instance_relative_config=True)

  # ensure the instance folder exists
  try:
      os.makedirs(app.instance_path)
  except OSError:
      pass

  from . import clab
  # URL handler
  @app.route('/collect/clab/<topology>/nodes/')
  def app_clab_node_data(topology):
    t = escape(topology)
    return clab.get_clab_node_data('./clab', t) # run flask from the parent directory

  return app