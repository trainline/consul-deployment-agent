# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

# Enum helper
class staticproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

# Py 2/3 compat enum
class HealthcheckTypes(object):
    @staticproperty
    def HTTP(cls):
        return 'healthcheck_http'
    @staticproperty
    def WIN_SERVICE(cls):
        return 'healthcheck_win_service'
    @staticproperty
    def WIN_PROCESS(cls):
        return 'healthcheck_win_process'
    @staticproperty
    def SCRIPT(cls):
        return 'healthcheck_script'
    @staticproperty
    def PLUGIN(cls):
        return 'healthcheck_plugin'
    @staticproperty
    def UNKNOWN(cls):
        return 'healthcheck_unknown'

# Common healthcheck utils
class HealthcheckUtils(object):
    
    @staticmethod
    def get_type(check):
        type = check.get('type')
        if type == 'http':
            return HealthcheckTypes.HTTP
        elif type == 'service':
            return HealthcheckTypes.WIN_SERVICE
        elif type == 'process':
            return HealthcheckTypes.WIN_PROCESS
        elif type == 'script':
            return HealthcheckTypes.SCRIPT
        elif type == 'plugin':
            return HealthcheckTypes.PLUGIN
        else:
            return HealthcheckTypes.UNKNOWN

    @staticmethod
    def get_http_url(check, service):
        url = check.get('http', '')
        port = service.port
        if port is not None and port is not 0:
            url = url.replace('${PORT}', str(port))
        return url

    @staticmethod
    def get_unique_name(check, service):
        check_name = check.get('name', 'unnamed-check')
        service_base = service.name.split('-')[1]
        unique_name = "{0}-{1}".format(service_base, check_name)
        slice = service.slice
        if slice != 'none' and slice is not None:
            slice_id = slice[0]
            unique_name = "{0}-{1}".format(unique_name, slice_id)
        return unique_name

