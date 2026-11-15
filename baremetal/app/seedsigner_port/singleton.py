# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
class Singleton:
    _instance = None

    def __init__(self):
        raise Exception('Cannot directly instantiate a Singleton. Access via get_instance()')

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

class ConfigurableSingleton(Singleton):

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        else:
            raise Exception('Must call %s.configure_instance() first' % cls.__name__)

    @classmethod
    def configure_instance(cls, config=None):
        if cls._instance:
            raise Exception('Instance already configured')
