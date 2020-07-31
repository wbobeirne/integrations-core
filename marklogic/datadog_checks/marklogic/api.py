# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from typing import Any, Dict, List

from datadog_checks.base.utils.http import RequestsWrapper

from .constants import RESOURCE_SINGULARS


class MarkLogicApi(object):
    def __init__(self, http, api_url):
        # type: (RequestsWrapper, str) -> None
        self._http = http
        self._base_url = api_url + '/manage/v2'

    def http_get(self, route="", params=None):
        # type: (str, Dict[str, str]) -> Dict[str, Any]
        if params is None:
            params = {}
        params['format'] = 'json'  # Always in json

        url = self._base_url + route
        resp = self._http.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_status_data(self, resource=None, name=None, group=None):
        # type: (str, str, str) -> Dict[str, Any]
        """
        Example url:
            - http://localhost:8002/manage/v2/hosts?view=status
            - http://localhost:8002/manage/v2/hosts?view=status&format=json (cluster level)
            - http://localhost:8002/manage/v2/forests/Security?view=status&format=json
            - http://localhost:8002/manage/v2/databases/Extensions?view=status&format=json
            - http://localhost:8002/manage/v2/hosts/2871b05b4bdc?view=status&format=json
            - http://localhost:8002/manage/v2/transactions?format=json
                (already in http://localhost:8002/manage/v2/hosts?view=status)
            - http://localhost:8002/manage/v2/servers?view=status&format=json
                (already in http://localhost:8002/manage/v2/hosts?view=status)
        """
        params = {'view': 'status'}
        route = ""
        if resource:
            route = "/" + resource
        if name:
            route += "/" + name
        if group:
            params['group-id'] = group

        return self.http_get(route, params)

    def get_requests_data(self, resource=None, name=None, group=None):
        # type: (str, str, str) -> Dict[str, Any]
        """
        https://docs.marklogic.com/REST/GET/manage/v2/requests
        Example url:
            - http://localhost:8002/manage/v2/requests?format=json (cluster level)
            - http://localhost:8002/manage/v2/requests?format=json&server-id=Admin&group-id=Default
            - http://localhost:8002/manage/v2/requests?format=json&group-id=Default
            - http://localhost:8002/manage/v2/requests?format=json&host-id=2871b05b4bdc
        """
        params = {}
        route = "/requests"
        if resource and name:
            params['{}-id'.format(resource)] = name
        if group:
            params['group-id'] = group

        return self.http_get(route, params)

    def get_storage_data(self, resource=None, name=None, group=None):
        # type: (str, str, str) -> Dict[str, Any]
        """
        Example url:
            - http://localhost:8002/manage/v2/forests?format=json&view=storage
            - http://localhost:8002/manage/v2/forests?format=json&view=storage&database-id=Last-Login
            - http://localhost:8002/manage/v2/forests?format=json&view=storage&forest-id=Last-Login
            - http://localhost:8002/manage/v2/forests?format=json&view=storage&database-id=Security
        """
        params = {
            'view': 'storage',
        }
        route = "/forests"
        if resource and name:
            params['{}-id'.format(resource)] = name
        if group:
            params['group-id'] = group

        return self.http_get(route, params)

    def get_resources(self):
        # type: () -> List[Dict[str, str]]
        data = self._get_raw_resources()
        resources = []  # type: List[Dict[str, str]]

        for group in data['cluster-query']['relations']['relation-group']:
            resource_type = group['typeref']
            for rel in group['relation']:
                resource_found = {
                    'id': rel['idref'],
                    'type': RESOURCE_SINGULARS.get(resource_type, resource_type),
                    'name': rel['nameref'],
                    'uri': rel['uriref'][len('/manage/v2') :],
                }

                if rel.get('qualifiers'):
                    # Making sure the group-id is in the qualifiers
                    for qualifier in rel['qualifiers']['qualifier']:
                        if 'group-id={}'.format(qualifier['nameref']) in rel['uriref']:
                            resource_found['group'] = qualifier['nameref']
                            break
                resources.append(resource_found)

        return resources

    def _get_raw_resources(self):
        # type: () -> Dict[str, Any]
        # This resource address returns the summary of all of the resources in the local cluster,
        # or resources in the local cluster that match a query.
        # http://localhost:8002/manage/v2?view=query&format=json
        params = {
            'view': 'query',
        }

        return self.http_get(params=params)

    def get_health(self):
        # type: () -> Dict[str, Any]
        """
        Return the cluster health querying http://localhost:8002/manage/v2?view=health&format=json.
        See https://docs.marklogic.com/REST/GET/manage/v2.
        """
        params = {'view': 'health'}

        return self.http_get(params=params)