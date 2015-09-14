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

import logging
import collections

import giza.jeerah.client
import rstcloth.rstcloth as rstcloth

logger = logging.getLogger('giza.content.changelog.views')

def get_changelog_content(fn, version, conf):
    jira = giza.jeerah.client.JeerahClient(conf)
    jira.connect()
    # jira.results_format = "dict"

    query = "project in ({0}) and fixVersion = {1}".format(', '.join(conf.system.files.data.jira.site.projects),
                                                           version)
    issues = jira.query(query)
    logger.info("building changelog for {0} with {1} issue(s)".format(version, len(issues)))

    headings = collections.OrderedDict()
    for k in conf.system.files.data.jira.changelog.ordering:
        headings[k] = list()

    groups = dict()
    for k, v in conf.system.files.data.jira.changelog.groups.items():
        for c in v:
            groups[c] = k

    nested = dict()
    for k, v in conf.system.files.data.jira.changelog.nesting.items():
        for c in v:
            nested[c] = k

    for issue in issues:
        components = [c.name for c in issue.fields.components]

        if len(components) == 0:
            headings['Internals'].append((issue.key, issue.fields.summary))
        else:
            headings[groups[components[0]]].append((issue.key, issue.fields.summary))

    r = rstcloth.RstCloth()
    level = 3

    r.heading(text="{0} Changelog".format(version), char=giza.content.helper.character_levels[level-1])
    r.newline()
    for heading, issues in headings.items():
        if heading in nested:
            continue
        else:
            if heading not in conf.system.files.data.jira.changelog.nesting and len(issues) == 0:
                continue

            r.heading(text=heading, indent=0,
                      char=giza.content.helper.character_levels[level])
            r.newline()


            if len(issues) == 1:
                r.content("{0} {1}".format(issues[0][1], r.role("issue", issues[0][0])), wrap=False)
            else:
                for issue in issues:
                    r.li("{0} {1}".format(issue[1], r.role("issue", issue[0])), wrap=False)

            r.newline()

            if heading in conf.system.files.data.jira.changelog.nesting:
                for sub in conf.system.files.data.jira.changelog.nesting[heading]:
                    if len(headings[sub]) == 0:
                        continue

                    r.heading(text=sub, indent=0,
                              char=giza.content.helper.character_levels[level+1])
                    r.newline()

                    sub_issues = headings[sub]
                    if len(sub_issues) == 0:
                        r.content("{0} {1}".format(issue[1].strip(), r.role("issue", issue[0])), wrap=False)
                    else:
                        for issue in sub_issues:
                            r.li("{0} {1}".format(issue[1].strip(), r.role("issue", issue[0])), wrap=False)
                    r.newline()

    r.write(fn)
    logger.info("wrote changelog to {0}. you must commit this file independently.".format(fn))


def render_intermediate_files(fn, version, releases):
    r = rstcloth.RstCloth()
    for rel in releases:
        r.directive("include", "/includes/changelogs/releases/{0}.rst".format('.'.join([str(s) for s in rel])))
        r.newline()

    r.write(fn)
    logger.info("wrote intermediate versions file ")
