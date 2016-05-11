# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>
   Ralph Bean <rbean@redhat.com>

"""

import xml2dict

from anitya.lib.backends import BaseBackend
from anitya.lib.exceptions import AnityaPluginException


def _get_versions(url):
    ''' Retrieve the versions for the provided url. '''
    try:
        req = PeclBackend.call_url(url)
    except Exception:  # pragma: no cover
        raise AnityaPluginException('Could not contact %s' % url)

    data = req.text
    versions = []
    for line in data.split('\n'):
        if '<v>' in line and '</v>' in line:
            version = line.split('v>', 2)[1].split('</')[0]
            versions.append(version)
    return versions


class PeclBackend(BaseBackend):
    ''' The custom class for projects hosted on pecl.php.net.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    '''

    name = 'PECL'
    examples = [
        'http://pecl.php.net/package/inotify',
        'http://pecl.php.net/package/gnupg',
    ]

    @classmethod
    def get_version(cls, project):
        ''' Method called to retrieve the latest version of the projects
        provided, project that relies on the backend of this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: the latest version found upstream
        :return type: str
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the version cannot be retrieved correctly

        '''
        return cls.get_versions(project)[0]

    @classmethod
    def get_versions(cls, project):
        ''' Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`model.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        '''
        url_template = 'https://pecl.php.net/rest/r/%(name)s/allreleases.xml'

        url = url_template % {'name': project.name.lower()}
        versions = []
        try:
            versions = _get_versions(url)
        except AnityaPluginException:
            pass

        if not versions and '-' in project.name:
            pname = project.name.lower().replace('-', '_')
            url = url_template % {'name': pname}
            versions = _get_versions(url)

        if not versions:
            raise AnityaPluginException(
                'No versions found for %s' % project.name.lower())

        return versions

    @classmethod
    def check_feed(cls):
        ''' Return a generator over the latest 10 uploads to PECL

        by querying an RSS feed.
        '''

        url = 'https://pecl.php.net/feeds/latest.rss'

        try:
            response = cls.call_url(url)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('Could not contact %s' % url)

        try:
            parser = xml2dict.XML2Dict()
            data = parser.fromstring(response.text)
        except Exception:  # pragma: no cover
            raise AnityaPluginException('No XML returned by %s' % url)

        items = data['RDF']['item']
        for entry in items:
            title = entry['title']['value']
            name, version = title.rsplit(None, 1)
            homepage = 'http://pecl.php.net/package/%s' % name
            yield name, homepage, cls.name, version
