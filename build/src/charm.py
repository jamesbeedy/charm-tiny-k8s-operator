#!/usr/bin/python3
import os
import logging

from collections import namedtuple
import yaml


from jinja2 import Environment, FileSystemLoader

# Operator Frmework imports go here
from ops.charm import CharmBase
from ops.main import main
from ops.model import (
    BlockedStatus,
    MaintenanceStatus,
    ModelError,
)


logger = logging.getLogger()


class TestK8sCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(
            self.on.start,
            self._on_start
        )

    def _on_start(self, event):
        logger.debug("################ LOGGING EVENT START ####################")

        name = self.meta.name
        image_meta = _get_image_meta("bitcoind", self)
        config = self.model.config

        spec = _make_pod_spec(name, image_meta, config) 
        self.model.pod.set_spec(spec)


def _make_pod_spec(name, image_info, config):

    def load_template(name, path=None):
        """ load template file
        :param str name: name of template file
        :param str path: alternate location of template location
        """
        env = Environment(
            loader=FileSystemLoader(os.path.join(_charm_dir(), 'templates')))
        return env.get_template(name)

    data = {
        'env': {},
        'name': name,
        'docker_image_path': image_info.registrypath,
        'docker_image_username': image_info.username,
        'docker_image_password': image_info.password,
    }
    for key, val in config.items():
        if key.startswith("btc"):
            data['env'][key.upper().replace("-", "_")] = val

    app_yml = load_template('spec_template.yaml')
    app_yml = app_yml.render(data=data)

    return app_yml


def _charm_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _get_image_meta(image_name, charm):
    resources_repo = charm.model.resources

    path = resources_repo.fetch(image_name)
    if not path.exists():
        msg = 'Resource not found at {}'.format(path)
        raise ResourceError(image_name, msg)

    resource_yaml = path.read_text()

    if not resource_yaml:
        msg = 'Resource unreadable at {}'.format(path)
        raise ResourceError(image_name, msg)

    try:
        resource_dict = yaml.safe_load(resource_yaml)
    except yaml.error.YAMLError:
        msg = 'Invalid YAML at {}'.format(path)
        raise ResourceError(image_name, msg)
    else:
        return ImageMeta(**resource_dict)


ImageMeta = namedtuple('ImageMeta',
                       [
                           'registrypath',
                           'username',
                           'password'
                       ])


class ResourceError(ModelError):

    def __init__(self, resource_name, message):
        super().__init__(resource_name)
        msg = "{}: {}".format('resource_name', 'message')
        self.status = BlockedStatus(msg)


if __name__ == "__main__":
    main(TestK8sCharm)
