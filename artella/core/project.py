#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaProject implementation
"""


class ArtellaProject(object):
    def __init__(self, session, project_id, name, client):
        super(ArtellaProject, self).__init__()

        self._session = session
        self._id = project_id
        self._name = name
        self._client = client

    # ==============================================================================================================
    # PROPERTIES
    # ==============================================================================================================

    @property
    def remote_session(self):
        return self._session

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    # ==============================================================================================================
    # CREATE
    # ==============================================================================================================

    @classmethod
    def create(cls, project_id, client):
        """
        Creates a new instance of the project taking into account th e given project ID

        :param str project_id: ID of the project
        :param ArtellaDriveClient client: Artella Drive Client this project is linked to
        :return: New instance of the project with the give ID. Exception is raised if project cannot be created
        :rtype: ArtellaProject
        """

        if not client:
            raise Exception(
                'Project with ID "{}" cannot be created because not Artella Drive Client instance was given'.format(
                    project_id))
        if not project_id:
            raise Exception('Project cannot be created because no ID was given')

        projects = client.get_remote_projects()

        new_project = None
        for remote_session, project_ids in projects.items():
            if project_id in project_ids:
                project_name = client.get_project_name(project_id)
                new_project = cls(session=remote_session, project_id=project_id, name=project_name, client=client)
                break

        if not new_project:
            raise Exception('Impossible to create project with ID: "{}"'.format(project_id))

        return new_project
