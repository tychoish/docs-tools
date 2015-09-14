# Copyright 2014 MongoDB, Inc.
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

import os.path
import logging

from libgiza.config import ConfigurationBase, RecursiveConfigurationBase

logger = logging.getLogger('giza.config.jeerah')


class JeerahConfig(RecursiveConfigurationBase):
    @property
    def buckets(self):
        if 'buckets' in self.state:
            return self.state['buckets']
        else:
            return {}

    @property
    def site(self):
        return self.state['site']

    @site.setter
    def site(self, value):
        if isinstance(value, JeerahSiteConfig):
            self.state['site'] = value
        else:
            self.state['site'] = JeerahSiteConfig(value)

    @property
    def changelog(self):
        return self.state['changelog']

    @changelog.setter
    def changelog(self, value):
        changelog_config = ConfigurationBase()
        changelog_config._option_registry = ["ordering", "nesting", "groups"]

        if isinstance(value, dict):
            if "source" in value:
                value = os.path.join(self.conf.paths.projectroot, self.conf.paths.global_config, value['source'])

            changelog_config.ingest(value)

            for k in ("ordering", "nesting", "groups"):
                if k not in changelog_config:
                    raise TypeError("changelog definition is incomplete")

            self.state["changelog"] = changelog_config
        else:
            raise TypeError("invalid changelog")


class JeerahSiteConfig(ConfigurationBase):
    _option_registry = ['url']

    @property
    def credentials(self):
        return self.state['credentials']

    @credentials.setter
    def credentials(self, value):
        value = os.path.expanduser(value)
        self.state['credentials'] = value

    @property
    def projects(self):
        return self.state['projects']

    @projects.setter
    def projects(self, value):
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, basestring):
                    raise TypeError("jira project {0} is not a string".format(value))

            self.state['projects'] = value
        else:
            raise TypeError("jira projects must be a list: {0}".format(value))

    @property
    def versions(self):
        return self.state["versions"]

    @versions.setter
    def versions(self, value):
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, basestring):
                    raise TypeError("jira version {0} is not a string".format(value))

                if len(item.split(".")) != 3:
                    raise TypeError("{0} is an invalid version".format(item))

            self.state['versions'] = value
        else:
            raise TypeError("jira versions must be a list: {0}".format(value))
