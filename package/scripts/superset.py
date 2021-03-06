# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path as path

from common import supersetHome, startCmdPrefixTmpl, startCmdSuffix
from resource_management.core.exceptions import ExecutionFailed, ComponentIsNotRunning
from resource_management.core.resources.system import Execute
from resource_management.libraries.script.script import Script


class Superset(Script):
    def install(self, env):
        Execute(
            'yum install -y gcc gcc-c++ libffi-devel python3-devel python3-pip python3-wheel openssl-devel cyrus-sasl-devel openldap-devel mysql-devel'
        )
        Execute('pip3 install virtualenv')

        Execute('mkdir -p {0}'.format(supersetHome))

        Execute('cd {0} && python3 -m venv venv'.format(supersetHome))

        self.configure(env)

        Execute(
            'export LC_ALL=en_US.UTF-8 && export LANG=en_US.UTF-8 && '
            'cd ' + supersetHome + ' && '
                                   '. venv/bin/activate && '
                                   'pip3 install --upgrade setuptools pip && '
                                   'pip3 install mysqlclient pyhive flask_cors gevent apache-superset && '
                                   'superset db upgrade && '
                                   'export FLASK_APP=superset && '
                                   'flask fab create-admin --username admin --password admin --firstname admin --lastname admin --email admin@admin.com && '
                                   'superset init '
        )

    def stop(self, env):
        startCmd = self.buildStartCmdPrefix() + startCmdSuffix
        Execute("ps -ef |grep -v grep | grep '" + startCmd + "'|awk '{print $2}' |xargs kill -9 ")

    def start(self, env):
        startCmd = self.buildStartCmdPrefix() + '"' + startCmdSuffix + '"'
        Execute(
            'cd ' + supersetHome + ' && '
                                   '. venv/bin/activate && nohup ' + startCmd + ' &'
        )

    def status(self, env):
        try:
            startCmd = self.buildStartCmdPrefix() + startCmdSuffix
            Execute(
                "export AZ_CNT=`ps -ef |grep -v grep |grep '" + startCmd + "' | wc -l` && `if [ $AZ_CNT -ne 0 ];then exit 0;else exit 3;fi `"
            )
        except ExecutionFailed as ef:
            if ef.code == 3:
                raise ComponentIsNotRunning("ComponentIsNotRunning")
            else:
                raise ef

    def configure(self, env):
        from params import superset_config
        key_val_template = '{0}={1}\n'
        with open(path.join(supersetHome + '/venv/lib/python3.6/site-packages', 'superset_config.py'), 'w') as f:
            for key, value in superset_config.iteritems():
                if key != 'content':
                    f.write(key_val_template.format(key, value))
            if superset_config.has_key('content'):
                f.write(str(superset_config['content']))

    def buildStartCmdPrefix(self):
        from params import superset_config
        return startCmdPrefixTmpl.format(superset_config['SUPERSET_WEBSERVER_PORT'])


if __name__ == '__main__':
    Superset().execute()
