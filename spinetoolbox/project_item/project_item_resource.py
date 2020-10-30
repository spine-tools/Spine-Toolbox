######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Provides the ProjectItemResource class.

:authors: M. Marin (KTH)
:date:   29.4.2020
"""
from urllib.parse import urlparse
from urllib.request import url2pathname


class _ResourceProvider:
    """A picklable class to hold information about a resource's provider.

    In multiprocess pipeline execution with dagster, ProjectItemResource needs to be pickled
    (because Outputs of solids are saved to disk for some reason), 
    which is *not possible* if one of the attributes is a ExecutableItemBase instance.
    Since all we ever use from the ProjectItemResource.provider is the name,
    this class works as an efficient replacement.

    More attributes can be added as needed (in case we need to know more about a resource's provider)
    making sure that this class remains picklable.
    """

    def __init__(self, item):
        """
        Args:
            item (ExecutableItemBase)
        """
        self.name = item.name


class ProjectItemResource:
    """Class to hold a resource made available by a project item
    and that may be consumed by another project item."""

    def __init__(self, provider, type_, url="", metadata=None):
        """
        Args:
            provider (ProjectItem or ExecutionItem): The item that provides the resource
            type_ (str): The resource type, currently available types:

                - "file": url points to the file's path
                - "database": url is the databases url
                - "transient_file": a file that may not yet be available or may change its location;
                  url points to latest version or is empty, metadata contains the "label" key
                  and an optional "pattern" key
                - "file_pattern": a file pattern with wildcards that acts as a placeholder;
                  url is empty, metadata contains the "label" key
            url (str): The url of the resource
            metadata (dict): Some metadata providing extra information about the resource.
                Currently available keys:

                - label (str): a textual label
                - pattern (str): a file pattern if the file is part of that pattern
        """
        self.provider = _ResourceProvider(provider)
        self.type_ = type_
        self.url = url
        self.parsed_url = urlparse(url)
        self.metadata = metadata if metadata is not None else dict()

    def __eq__(self, other):
        if not isinstance(other, ProjectItemResource):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return (
            self.provider == other.provider
            and self.type_ == other.type_
            and self.url == other.url
            and self.metadata == other.metadata
        )

    def __repr__(self):
        result = "ProjectItemResource("
        result += f"provider={self.provider.name}, "
        result += f"type_={self.type_}, "
        result += f"url={self.url}, "
        result += f"metadata={self.metadata})"
        return result

    @property
    def path(self):
        """Returns the resource path in the local syntax, as obtained from parsing the url."""
        return url2pathname(self.parsed_url.path)

    @property
    def scheme(self):
        """Returns the resource scheme, as obtained from parsing the url."""
        return self.parsed_url.scheme
