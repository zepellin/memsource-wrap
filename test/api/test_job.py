from unittest.mock import patch, PropertyMock
from memsource import api, models, exceptions, constants
import requests
import os
import os.path
import uuid
import api as api_test


class TestApiJob(api_test.ApiTestCase):
    def setUp(self):
        self.url_base = 'https://cloud1.memsource.com/web/api/v6/job'
        self.job = api.Job(None)
        self.test_file_path = '/tmp/test_file.txt'
        self.test_file_copy_path = '/var/tmp/test_file.txt'
        self.test_file_uuid1_name = 'test-file-uuid1'
        self.test_file_uuid1_path = '/var/tmp/{},txt'.format(self.test_file_uuid1_name)

        self.setCleanUpFiles((
            self.test_file_path,
            self.test_file_copy_path,
            self.test_file_uuid1_path,
        ))

        with open(self.test_file_path, 'w+') as f:
            f.write('This is test file.')

        self.create_return_value = {
            'jobParts': [{
                'id': 9371,
                'task': '5023cd08e4b015e0656c4a8f',
                'fileName': 'test_file.txt',
                'targetLang': 'ja',
                'wordCount': 121,
                'beginIndex': 0,
                'endIndex': 14
            }, {
                'id': 9372,
                'task': '5087ab08eac015e0656c4a00',
                'fileName': 'test_file.txt',
                'targetLang': 'ja',
                'wordCount': 121,
                'beginIndex': 0,
                'endIndex': 14
            }]
        }

    @patch.object(requests, 'request')
    def test_create(self, mock_request):
        type(mock_request()).status_code = PropertyMock(return_value=200)
        mock_request().json.return_value = self.create_return_value

        target_lang = 'ja'
        project_id = self.gen_random_int()

        returned_value = self.job.create(project_id, self.test_file_path, target_lang)

        # Don't use assert_called_with because files has file object. It is difficult to test.
        self.assertTrue(mock_request.called)
        (called_args, called_kwargs) = mock_request.call_args

        # hard to test
        del called_kwargs['files']
        self.assertEqual(('post', '{}/create'.format(self.url_base)), called_args)

        self.assertEqual({
            'params': {
                'token': self.job.token,
                'project': project_id,
                'targetLang': target_lang,
            },
            'timeout': constants.Base.timeout.value,
        }, called_kwargs)

        self.assertEqual(2, len(returned_value))
        for job_part in returned_value:
            self.assertIsInstance(job_part, models.JobPart)

    @patch.object(requests, 'request')
    def test_create_with_unsupported_file(self, mock_request):
        type(mock_request()).status_code = PropertyMock(return_value=200)
        mock_request().json.return_value = {
            'unsupportedFiles': ['test_file.txt'],
        }

        self.assertRaises(
            exceptions.MemsourceUnsupportedFileException,
            lambda: self.job.create(self.gen_random_int(), self.test_file_path, 'ja')
        )

        # Check the copy exists
        self.assertTrue(os.path.isfile(self.test_file_copy_path))

    @patch.object(uuid, 'uuid1')
    @patch.object(requests, 'request')
    def test_create_from_text(self, mock_request, mock_uuid1):
        type(mock_request()).status_code = PropertyMock(return_value=200)
        mock_request().json.return_value = self.create_return_value
        mock_uuid1().hex.return_value = PropertyMock(return_value=self.test_file_uuid1_name)

        target_lang = 'ja'
        project_id = self.gen_random_int()

        returned_value = self.job.createFromText(project_id, self.test_file_path, target_lang)

        # Don't use assert_called_with because files has file object. It is difficult to test.
        self.assertTrue(mock_request.called)
        (called_args, called_kwargs) = mock_request.call_args

        del called_kwargs['files']
        self.assertEqual(('post', '{}/create'.format(self.url_base)), called_args)

        self.assertEqual({
            'params': {
                'token': self.job.token,
                'project': project_id,
                'targetLang': target_lang,
            },
            'timeout': constants.Base.timeout.value,
        }, called_kwargs)

        self.assertEqual(2, len(returned_value))
        for job_part in returned_value:
            self.assertIsInstance(job_part, models.JobPart)

    @patch.object(requests, 'request')
    def test_list_by_project(self, mock_request):
        type(mock_request()).status_code = PropertyMock(return_value=200)

        project_id = self.gen_random_int()

        mock_request().json.return_value = [{
            'targetLang': 'de',
            'endIndex': 14,
            'project': {
                'domain': None,
                'machineTranslateSettings': None,
                'status': 'NEW',
                'name': 'project',
                'note': None,
                'dateDue': None,
                'sourceLang': 'en',
                'client': None,
                'subDomain': None,
                'id': project_id,
                'targetLangs': ['ja'],
                'workflowSteps': [],
                'dateCreated': '2013-10-31T10:15:05Z'
            },
            'isParentJobSplit': False,
            'beginIndex': 0,
            'task': 'U8llA7UOMiKGJ8Dk',
            'dateDue': None,
            'fileName': 'small.properties',
            'assignedTo': {
                'email': 'test@test.com',
                'firstName': 'linguist',
                'id': 2,
                'lastName': 'test',
                'role': 'LINGUIST',
                'userName': 'linguist',
                'active': True
            },
            'id': 1,
            'wordsCount': 331,
            'status': 'NEW',
            'dateCreated': '2013-10-31T10:15:06Z',
            'workflowLevel': 1
        }]

        returned_value = self.job.listByProject(project_id)

        for job_part in returned_value:
            self.assertIsInstance(job_part, models.JobPart)

        mock_request.assert_called_with(
            'post',
            '{}/listByProject'.format(self.url_base),
            params={
                'token': self.job.token,
                'project': project_id
            },
            files={},
            timeout=constants.Base.timeout.value
        )

        self.assertEqual(len(returned_value), len(mock_request().json()))