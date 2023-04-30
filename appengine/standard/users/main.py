# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sample Google App Engine application that demonstrates using the Users API

For more information about App Engine, see README.md under /appengine.
"""

# [START all]

from google.appengine.api import users
import webapp2


class MainPage(webapp2.RequestHandler):
    def get(self):
        if user := users.get_current_user():
            nickname = user.nickname()
            logout_url = users.create_logout_url('/')
            greeting = f'Welcome, {nickname}! (<a href="{logout_url}">sign out</a>)'
        else:
            login_url = users.create_login_url('/')
            greeting = f'<a href="{login_url}">Sign in</a>'
        # [END user_details]
        self.response.write(f'<html><body>{greeting}</body></html>')


class AdminPage(webapp2.RequestHandler):
    def get(self):
        if user := users.get_current_user():
            if users.is_current_user_admin():
                self.response.write('You are an administrator.')
            else:
                self.response.write('You are not an administrator.')
        else:
            self.response.write('You are not logged in.')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/admin', AdminPage)
], debug=True)

# [END all]
