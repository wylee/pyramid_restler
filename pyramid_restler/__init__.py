from pyramid_restler.config import add_restful_views, enable_POST_tunneling


def includeme(config):
    config.add_directive('add_restful_views', add_restful_views)
    config.add_directive('enable_POST_tunneling', enable_POST_tunneling)
