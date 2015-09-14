# Copyright 2015 MongoDB, Inc.
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

import giza.content.changelog.views

from giza.config.content import new_content_type
from libgiza.task import Task

logger = logging.getLogger('giza.content.changelog.tasks')


def register_changelogs(conf):
    content_dfn = new_content_type(name='changelogs',
                                   task_generator=changelog_tasks,
                                   conf=conf)

    conf.system.content.add(name='changelogs', definition=content_dfn)


def get_major_version_groupings(versions):
    major_versions = {}
    for v in versions:
        parts = [int(i) for i in v.split(".")]
        mver = ".".join([str(s) for s in parts[0:2]])
        if mver not in major_versions:
            major_versions[mver] = [parts]
        else:
            major_versions[mver].append(parts)

    for v in major_versions.values():
        v.sort(reverse=True)

    return major_versions


def changelog_tasks(conf):
    tasks = []

    jira_config = os.path.join(conf.paths.projectroot, conf.paths.builddata, "jira.yaml")
    major_versions = get_major_version_groupings(conf.system.files.data.jira.site.versions)
    for version, releases in major_versions.items():
        fn = os.path.join(conf.paths.projectroot, conf.paths.includes, "changelogs", version + ".rst")
        t = Task(job=giza.content.changelog.views.render_intermediate_files,
                 args=(fn, version, releases),
                 target=fn,
                 dependency=[jira_config])
        tasks.append(t)

    if conf.git.branches.current != "master":
        logger.error("you must generate changelogs on the master branch and them backport them to another branch.")
        return tasks

    if not os.path.exists(os.path.expanduser(conf.system.files.data.jira.site.credentials)):
        logger.warning("jira credentials are not configured for your user. not generating changelog tasks")
        return tasks

    for version in  conf.system.files.data.jira.site.versions:
        fn = os.path.join(conf.paths.projectroot, conf.paths.includes, "changelogs", "releases", version + ".rst")
        t = Task(job=giza.content.changelog.views.get_changelog_content,
                 args=(fn, version, conf),
                 dependency=[jira_config],
                 target=fn)
        tasks.append(t)

    return tasks
