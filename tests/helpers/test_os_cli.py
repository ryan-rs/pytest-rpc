# -*- coding: utf-8 -*-

"""Test cases for the 'os_cli*' helper functions."""

# ==============================================================================
# Imports
# ==============================================================================
import json
import pytest
import testinfra.host
import pytest_rpc.helpers
import testinfra.backend.base


# ==============================================================================
# Tests
# ==============================================================================
def test_os_cli_happy_path(mocker):
    """Verify that a valid call to the OpenStack CLI will work as expected.

    Args:
        mocker (pytest_mock.MockFixture): Mocking fixture.
    """

    # Setup
    fake_backend = mocker.Mock(spec=testinfra.backend.base.BaseBackend)
    myhost = testinfra.host.Host(fake_backend)

    command_result = mocker.Mock(spec=testinfra.backend.base.CommandResult)
    command_result.rc = 0
    command_result.stdout = 'So many images!'

    mocker.patch('testinfra.host.Host.run', return_value=command_result)

    # Expect
    subcmd = 'image list'
    expected_run_cmd = ("openstack {} --os-cloud default ".format(subcmd))

    # Test
    result = pytest_rpc.helpers.os_cli(myhost, subcmd)
    # noinspection PyUnresolvedReferences
    myhost.run.assert_called_with(expected_run_cmd)

    assert result == command_result.stdout


def test_os_cli_extra_options(mocker):
    """Verify that the OpenStack CLI can be called with extra options.

    Args:
        mocker (pytest_mock.MockFixture): Mocking fixture.
    """

    # Setup
    fake_backend = mocker.Mock(spec=testinfra.backend.base.BaseBackend)
    myhost = testinfra.host.Host(fake_backend)
    opts = ['-v', '--debug']

    command_result = mocker.Mock(spec=testinfra.backend.base.CommandResult)
    command_result.rc = 0
    command_result.stdout = 'So many images!'

    mocker.patch('testinfra.host.Host.run', return_value=command_result)

    # Expect
    subcmd = 'image list'
    expected_run_cmd = ("openstack {} "
                        "--os-cloud default "
                        "{} {}".format(subcmd, opts[0], opts[1]))

    # Test
    result = pytest_rpc.helpers.os_cli(myhost, subcmd, opts)
    # noinspection PyUnresolvedReferences
    myhost.run.assert_called_with(expected_run_cmd)

    assert result == command_result.stdout


def test_os_cli_unexpected_exit_code(mocker):
    """Verify that a call resulting in an unexpected exit code will result in
    an assertion failure.

    Args:
        mocker (pytest_mock.MockFixture): Mocking fixture.
    """

    # Setup
    fake_backend = mocker.Mock(spec=testinfra.backend.base.BaseBackend)
    myhost = testinfra.host.Host(fake_backend)

    command_result = mocker.Mock(spec=testinfra.backend.base.CommandResult)
    command_result.rc = 1
    command_result.stdout = 'Not the images you are looking for!'

    mocker.patch('testinfra.host.Host.run', return_value=command_result)

    # Expect
    subcmd = 'image list'
    expected_run_cmd = ("openstack {} --os-cloud default ".format(subcmd))

    # Test
    with pytest.raises(AssertionError):
        pytest_rpc.helpers.os_cli(myhost, subcmd)
    # noinspection PyUnresolvedReferences
    myhost.run.assert_called_with(expected_run_cmd)


def test_os_cli_json_happy_path(mocker):
    """Verify that the OpenStack CLI can be called with JSON formatting enabled.

    Args:
        mocker (pytest_mock.MockFixture): Mocking fixture.
    """

    # Setup
    fake_backend = mocker.Mock(spec=testinfra.backend.base.BaseBackend)
    myhost = testinfra.host.Host(fake_backend)

    command_result = mocker.Mock(spec=testinfra.backend.base.CommandResult)
    command_result.rc = 0
    command_result.stdout = '{"test": "test"}'

    mocker.patch('testinfra.host.Host.run', return_value=command_result)

    # Expect
    subcmd = 'image list'
    expected_run_cmd = ("openstack {} "
                        "--os-cloud default -f json".format(subcmd))

    # Test
    result = pytest_rpc.helpers.os_cli_json(myhost, subcmd)
    # noinspection PyUnresolvedReferences
    myhost.run.assert_called_with(expected_run_cmd)

    assert result == json.loads(command_result.stdout)


def test_os_cli_json_extra_options(mocker):
    """Verify that the OpenStack CLI can be called with extra options
    and with JSON formatting enabled.

    Args:
        mocker (pytest_mock.MockFixture): Mocking fixture.
    """

    # Setup
    fake_backend = mocker.Mock(spec=testinfra.backend.base.BaseBackend)
    myhost = testinfra.host.Host(fake_backend)
    opts = ['-v', '--debug']

    command_result = mocker.Mock(spec=testinfra.backend.base.CommandResult)
    command_result.rc = 0
    command_result.stdout = '{"test": "test"}'

    mocker.patch('testinfra.host.Host.run', return_value=command_result)

    # Expect
    subcmd = 'image list'
    expected_run_cmd = ("openstack {} "
                        "--os-cloud default "
                        "{} {} -f json".format(subcmd, opts[0], opts[1]))

    # Test
    result = pytest_rpc.helpers.os_cli_json(myhost, subcmd, opts)
    # noinspection PyUnresolvedReferences
    myhost.run.assert_called_with(expected_run_cmd)

    assert result == json.loads(command_result.stdout)
