import sys
import unittest
import flexmock
from validator import support


class TestSupport(unittest.TestCase):

    def test_load_group_config_for(self):
        fake_group_yaml = """
        key_1: value_1
        key_2: value_2
        """
        expected = {'key_1': 'value_1', 'key_2': 'value_2'}

        mock_builtin_open('./group.yml', fake_group_yaml)
        actual = support.load_group_config_for('images/x.yml')
        self.assertEqual(actual, expected)

        mock_builtin_open('../../group.yml', fake_group_yaml)
        actual = support.load_group_config_for('../../rpms/x.yml')
        self.assertEqual(actual, expected)

        mock_builtin_open('/var/lib/group.yml', fake_group_yaml)
        actual = support.load_group_config_for('/var/lib/images/x.yml')
        self.assertEqual(actual, expected)

    def test_get_ocp_build_data_dir(self):
        _dir = support.get_ocp_build_data_dir('/a/b/ocp-build-data/rpms/x.yml')
        self.assertEqual(_dir, '/a/b/ocp-build-data')

        _dir = support.get_ocp_build_data_dir('../rpms/foo.yml')
        self.assertEqual(_dir, '..')

        _dir = support.get_ocp_build_data_dir('rpms/foo.yml')
        self.assertEqual(_dir, '.')

    def test_get_artifact_type_image(self):
        artifact_type = support.get_artifact_type('/path/to/images/x.yml')
        self.assertEqual(artifact_type, 'image')

        artifact_type = support.get_artifact_type('../images/x.yml')
        self.assertEqual(artifact_type, 'image')

        artifact_type = support.get_artifact_type('images/x.yml')
        self.assertEqual(artifact_type, 'image')

    def test_get_artifact_type_rpm(self):
        artifact_type = support.get_artifact_type('/path/to/rpms/x.yml')
        self.assertEqual(artifact_type, 'rpm')

        artifact_type = support.get_artifact_type('../rpms/x.yml')
        self.assertEqual(artifact_type, 'rpm')

        artifact_type = support.get_artifact_type('rpms/x.yml')
        self.assertEqual(artifact_type, 'rpm')

    def test_get_artifact_type_unknown(self):
        artifact_type = support.get_artifact_type('/path/to/unknown/x.yml')
        self.assertEqual(artifact_type, '???')

        artifact_type = support.get_artifact_type('../images-on-path/x.yml')
        self.assertEqual(artifact_type, '???')

        artifact_type = support.get_artifact_type('unknown/rpms-on-name.yml')
        self.assertEqual(artifact_type, '???')

    def test_get_valid_streams_for(self):
        fake_streams_yaml = """
        cobol:
          image: openshift/cobol-builder:latest
        fortran:
          image: openshift/fortran-builder:latest
        """
        mock_builtin_open('./streams.yml', fake_streams_yaml)

        streams = support.get_valid_streams_for('images/x.yml')
        self.assertEqual(streams, {'cobol', 'fortran'})

    def test_get_valid_member_references_for(self):
        (flexmock(support.os)
            .should_receive('listdir')
            .with_args('./images')
            .and_return({'image-a', 'image-b', 'image-c'}))

        references = support.get_valid_member_references_for('images/x.yml')
        self.assertEqual(references, {'image-a', 'image-b', 'image-c'})

    def test_resource_exists(self):
        for status_code in [200, 204, 302, 304, 307, 308]:
            (flexmock(support.requests)
                .should_receive('head')
                .and_return(flexmock(status_code=status_code)))
            self.assertTrue(support.resource_exists('http://a.random/url'))

        for status_code in [400, 401, 403, 404, 405, 410]:
            (flexmock(support.requests)
                .should_receive('head')
                .and_return(flexmock(status_code=status_code)))
            self.assertFalse(support.resource_exists('http://a.random/url'))

    def test_resource_is_reacheable(self):
        (flexmock(support.requests)
            .should_receive('head')
            .replace_with(lambda _: None))
        self.assertTrue(support.resource_is_reacheable('http://a.random/url'))

        (flexmock(support.requests)
            .should_receive('head')
            .and_raise(support.requests.exceptions.ConnectionError))
        self.assertFalse(support.resource_is_reacheable('http://a.random/url'))


def mock_builtin_open(file, contents):
    mock = flexmock(get_builtin_module())
    mock.should_call('open')
    (mock.should_receive('open')
        .with_args(file)
        .and_return(flexmock(read=lambda: contents)))


def get_builtin_module():
    return sys.modules.get('__builtin__', sys.modules.get('builtins'))