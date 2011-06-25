from pyramid_restler.config import add_restful_routes, enable_POST_tunneling


def includeme(config):
    config.add_directive('add_restful_routes', add_restful_routes)
    config.add_directive('enable_POST_tunneling', enable_POST_tunneling)
