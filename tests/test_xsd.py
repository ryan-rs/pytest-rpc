# -*- coding: utf-8 -*-

"""Test cases for the 'get_xsd' utility function for retrieving the XSD for the project."""

# ======================================================================================================================
# Imports
# ======================================================================================================================
from __future__ import absolute_import
from lxml import etree
from pytest_rpc import ENV_VARS, get_xsd
from tests.conftest import run_and_parse

# ======================================================================================================================
# Globals
# ======================================================================================================================
TEST_ENV_VARS = list(ENV_VARS)      # Shallow copy.


# ======================================================================================================================
# Tests
# ======================================================================================================================
def test_happy_path(testdir, properly_decorated_test_function):
    """Verify that 'get_xsd' returns an XSD stream that can be used to validate JUnitXML."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_happy_path',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    xmlschema.assertValid(xml_doc)


def test_multiple_jira_references(testdir):
    """Verify that 'get_xsd' returns an XSD stream when a testcase is decorated Jira mark with multiple
    arguments.
    """

    # Setup
    testdir.makepyfile("""
                import pytest
                @pytest.mark.jira('ASC-123', 'ASC-124')
                @pytest.mark.test_id('123e4567-e89b-12d3-a456-426655440000')
                def test_xsd():
                    pass
    """)

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    xmlschema.assertValid(xml_doc)


def test_missing_global_property(testdir, properly_decorated_test_function, mocker):
    """Verify that XSD will enforce the presence of all required global test suite properties."""

    # Mock
    # Missing 'BUILD_URL'
    mock_env_vars = [x for x in TEST_ENV_VARS if x != 'BUILD_URL']

    mocker.patch('pytest_rpc.ENV_VARS', mock_env_vars)

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_missing_global',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_extra_global_property(testdir, properly_decorated_test_function, mocker):
    """Verify that XSD will enforce the strict presence of only required global test suite properties."""

    # Mock
    # Extra 'BUILD_URL'
    mock_env_vars = TEST_ENV_VARS + ['BUILD_URL']

    mocker.patch('pytest_rpc.ENV_VARS', mock_env_vars)

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_extra_global',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_typo_global_property(testdir, properly_decorated_test_function, mocker):
    """Verify that XSD will enforce the only certain property names are allowed for the test suite."""

    # Mock
    # Typo for RPC_RELEASE
    mock_env_vars = [x for x in TEST_ENV_VARS if x != 'RPC_RELEASE'] + ['RCP_RELEASE']

    mocker.patch('pytest_rpc.ENV_VARS', mock_env_vars)

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_typo_global',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_missing_required_marks(testdir, undecorated_test_function):
    """Verify that XSD will enforce the presence of 'test_id' and 'jira_id' properties for test cases."""

    # Setup
    testdir.makepyfile(undecorated_test_function.format(test_name='test_typo_global'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_missing_uuid_mark(testdir, single_decorated_test_function):
    """Verify that XSD will enforce the presence of 'test_id' property for test cases."""

    # Setup
    testdir.makepyfile(single_decorated_test_function.format(test_name='test_missing_uuid',
                                                             mark_type='jira',
                                                             mark_arg='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_missing_jira_mark(testdir, single_decorated_test_function):
    """Verify that XSD will enforce the presence of 'jira' property for test cases."""

    # Setup
    testdir.makepyfile(single_decorated_test_function.format(test_name='test_missing_jira',
                                                             mark_type='test_id',
                                                             mark_arg='123e4567-e89b-12d3-a456-426655440000'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_extra_testcase_property(testdir, properly_decorated_test_function):
    """Verify that XSD will enforce the strict presence of only required test case properties."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_extra_mark',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc

    # Add another property element for the testcase.
    xml_doc.find('./testcase/properties').append(etree.Element('property',
                                                               attrib={'name': 'extra', 'value': 'fail'}))
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_typo_property(testdir, properly_decorated_test_function):
    """Verify that XSD will enforce the only certain property names are allowed for the testcase."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_typo_mark',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc

    # Add another property element for the testcase.
    xml_doc.find('./testcase/properties/property').attrib['name'] = 'wrong_test_id'
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False
