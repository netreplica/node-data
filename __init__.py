import os

from flask import Flask, escape, request

def create_app(config=None):
  # create and configure the app
  app = Flask(__name__, instance_relative_config=True)
  app.config.from_mapping(
    ROOT='.',
  )
  
  if config is None:
    # load the instance config, if it exists
    app.config.from_pyfile(__name__ + '.cfg', silent=True)
  else:
    # load the config if passed in
    app.config.from_mapping(config)

  from . import clab
  # URL handler
  @app.route('/collect/clab/<topology>/nodes/')
  def app_clab_node_data(topology):
    t = escape(topology)
    return clab.get_clab_node_data(app.config['ROOT'], t)

  return app