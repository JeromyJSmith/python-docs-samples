# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sample App Engine application demonstrating how to connect to Google Cloud SQL
using App Engine's native unix socket or using TCP when running locally.

For more information, see the README.md.
"""

# [START gae_python_mysql_app]
import os

import MySQLdb
import webapp2


# These environment variables are configured in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')


def connect_to_cloudsql():
    if not os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        return MySQLdb.connect(
            host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD
        )

    # Connect using the unix socket located at
    # /cloudsql/cloudsql-connection-name.
    cloudsql_unix_socket = os.path.join(
        '/cloudsql', CLOUDSQL_CONNECTION_NAME)

    return MySQLdb.connect(
        unix_socket=cloudsql_unix_socket,
        user=CLOUDSQL_USER,
        passwd=CLOUDSQL_PASSWORD,
    )


class MainPage(webapp2.RequestHandler):
    def get(self):
        """Simple request handler that shows all of the MySQL variables."""
        self.response.headers['Content-Type'] = 'text/plain'

        db = connect_to_cloudsql()
        cursor = db.cursor()
        cursor.execute('SHOW VARIABLES')

        for r in cursor.fetchall():
            self.response.write(f'{r}\n')


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

# [END gae_python_mysql_app]
