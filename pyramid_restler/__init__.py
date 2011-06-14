from pyramid_restler.config import add_restful_routes


def includeme(config):
    config.add_directive('add_restful_routes', add_restful_routes)
