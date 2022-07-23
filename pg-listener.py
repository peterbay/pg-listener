#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) Petr Vavrin (peterbay) 2022

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import sys
import psycopg2
import configparser
import yaml
import json
import argparse
import select
import time

class pgListener:
    config = None
    dsn = None
    listen_list = []

    def __init__(self, argv):
        parser = argparse.ArgumentParser()
        parser.error = self.argsError
        parser.add_argument('--config', '-c', help='Config file')
        parser.add_argument('--json', '-j', action='store_true', help='Parse JSON message')
        parser.add_argument('--raw', '-r', action='store_true', help='Print raw message to stdout')

        self.args = parser.parse_args()

        if not self.args.config:
            self.exit(1, 'ERROR: Missing config file')

        self.loadConfig()
        self.listen()

    def exit(self, state = None, message = None):
        if message:
            sys.stdout.write(f'{message}\n')

        if state:
            sys.exit(state)

    def argsError(self, error):
        pass

    def loadConfig(self):
        config_extension = os.path.splitext(self.args.config)[1]

        if not config_extension:
            self.exit(1, 'ERROR: Missing config file extension')

        if config_extension == '.ini' or config_extension == '.conf':
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.args.config)

                self.dsn = self.config.get('database', 'dsn')
                listen = self.config.items('listen')

                if listen:
                    self.listen_list = [lis[0] for lis in listen if lis[1] == 'true']

            except Exception as e:
                self.exit(1, f'ERROR: Config parser error: {e}')

        elif config_extension == '.yaml':
            try:
                with open(self.args.config, 'r') as stream:
                    self.config = yaml.safe_load(stream)

                    database = self.config.get('database', None)
                    if database:
                        self.dsn = database.get('dsn', None)

                    listen = self.config.get('listen')

                    if listen:
                        self.listen_list = [key for key, value in listen.items() if value]

            except Exception as e:
                self.exit(1, f'ERROR: Yaml parser error: {e}')

        else:
            self.exit(1, 'ERROR: Wrong config file format. YAML and INI is supported')


    def listen(self):
        if not self.dsn:
            self.exit(1, 'ERROR: Missing database/dsn')

        try:
            connection = psycopg2.connect(self.dsn)
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = connection.cursor()

            for lis in self.listen_list:
                if not self.args.raw:
                    sys.stdout.write(f'LISTEN: {lis}\n')
                cur.execute(f'LISTEN {lis};')

            while True:
                select.select([connection],[],[])
                connection.poll()

                while connection.notifies:
                    notification_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    notification =  connection.notifies.pop()

                    if self.args.raw:
                        sys.stdout.write(f'{notification.payload}\n')
                        continue

                    payload = notification.payload
                    payload_delimiter = ''

                    if self.args.json:
                        try:
                            json_content = json.loads(payload)
                            payload = json.dumps(json_content, indent=4, sort_keys=True)
                            payload_delimiter = '\n'
                        except:
                            pass

                    sys.stdout.write(f'{notification_time} [{notification.pid}] {notification.channel}: {payload_delimiter}{payload}\n')

        except KeyboardInterrupt:
            try:
                connection.close()
            except:
                pass
            self.exit(0, '\nExit')

        except Exception as e:
            self.exit(1, f'Error: {e}')

if __name__ == '__main__':
    listener = pgListener(sys.argv)
