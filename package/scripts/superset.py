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
            'export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 SUPERSET_HOME=' + supersetHome + ' && '
                                                                                         'cd ' + supersetHome + ' && '
                                                                                                                '. venv/bin/activate && '
                                                                                                                'pip3 install --upgrade setuptools pip && '
                                                                                                                'pip3 install mysqlclient pyhive flask_cors gevent apache-superset requests && '
                                                                                                                'superset db upgrade && '
                                                                                                                'export FLASK_APP=superset && '
                                                                                                                'flask fab create-admin --username admin --password admin --firstname admin --lastname admin --email admin@admin.com && '
                                                                                                                'superset init '
        )

    def stop(self, env):
        Execute("ps -ef |grep -v grep | grep '" + startCmdSuffix + "'|awk '{print $2}' |xargs kill -9 ")

    def start(self, env):
        port = self.configure(env)
        startCmd = startCmdPrefixTmpl.format(port) + '"' + startCmdSuffix + '"'
        Execute(
            'export SUPERSET_HOME=' + supersetHome + ' && '
                                                     'cd $SUPERSET_HOME && '
                                                     '. venv/bin/activate && nohup ' + startCmd + ' > superset.out 2>&1 &'
        )

    def status(self, env):
        try:
            Execute(
                "export AZ_CNT=`ps -ef |grep -v grep |grep '" + startCmdSuffix + "' | wc -l` && `if [ $AZ_CNT -ne 0 ];then exit 0;else exit 3;fi `"
            )
        except ExecutionFailed as ef:
            if ef.code == 3:
                raise ComponentIsNotRunning("ComponentIsNotRunning")
            else:
                raise ef

    def configure(self, env):
        from params import superset_config
        key_val_template = '{0}={1}\n'
        port = ''
        with open(path.join(supersetHome + '/venv/lib/python3.6/site-packages', 'superset_config.py'), 'w') as f:
            for key, value in superset_config.iteritems():
                if key != 'content':
                    f.write(key_val_template.format(key, value))
                if key == 'SUPERSET_WEBSERVER_PORT':
                    port = value
            if superset_config.has_key('content'):
                f.write(str(superset_config['content']))
        return port


if __name__ == '__main__':
    Superset().execute()
