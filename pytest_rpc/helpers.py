# -*- coding: utf-8 -*-

# ==============================================================================
# Imports
# ==============================================================================
import re
import json
import uuid
from time import sleep


# ==============================================================================
# Private Functions
# ==============================================================================
def _delete_it(run_on_host,
               resource_type,
               resource_id,
               retries=10,
               addl_flags=''):
    """Delete an OpenStack resource.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack object type to query for.
        resource_id (uuid.UUID): The ID of the OpenStack object to query for.
        retries (int): The maximum number of retry attempts.
        addl_flags (str): Additional flags to pass to the OpenStack command.

    Returns:
        bool: True if the resource was successfully deleted, otherwise False.

    Raises:
        AssertionError: Failed to delete resource!
    """

    __tracebackhide__ = True

    sleep_timeout = 2
    cmd = (". ~/openrc ; "
           "openstack {} delete "
           "{} "
           "{}".format(resource_type, addl_flags, resource_id))
    assert_msg = ("Failed to delete resource type '{}' with given ID '{}'"
                  "!".format(resource_type, resource_id))

    assert run_on_container(run_on_host, cmd, 'utility').rc == 0, assert_msg

    for i in range(0, retries):
        try:
            assert_resource_exists_by_id(run_on_host,
                                         resource_type,
                                         resource_id)
        except AssertionError:
            return True     # If assertion fails then the resource is deleted.

        sleep(sleep_timeout)

    return False


# ==============================================================================
# Public Functions
# ==============================================================================
def assert_resource_attribute_value(run_on_host,
                                    resource_type,
                                    resource_id,
                                    attribute_name,
                                    expected_value,
                                    retries=10,
                                    case_insensitive=True):
    """Assert that an OpenStack resource attribute has expected value.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.
        resource_type (str): The OpenStack resource type to query for.
        resource_id (uuid.UUID): The name of the OpenStack resource ID to
            query for.
        attribute_name (str): The OpenStack resource attribute to inspect for
            expected value.
        expected_value (str): The expected value for the OpenStack resource
            attribute.
        retries (int): The maximum number of retry attempts.
        case_insensitive (bool): Flag for controlling whether to match case
            sensitive or not for 'expected_value'.

    Raises:
        AssertionError: No resources of the given type found!
    """

    __tracebackhide__ = True

    sleep_timeout = 6
    resource = {}
    expectation_met = False

    for i in range(0, retries):
        try:
            resource = get_resource_by_id(run_on_host,
                                          resource_type,
                                          resource_id)
        except RuntimeError as e:
            raise AssertionError(str(e))

        if attribute_name not in resource:
            raise AssertionError(
                "Attribute '{}' for resource type '{}'"
                "with ID '{}' does not "
                "exist!".format(attribute_name, resource_type, resource_id)
            )

        if resource[attribute_name] == expected_value:
            expectation_met = True
        elif resource[attribute_name].lower() == expected_value \
                and case_insensitive:
            expectation_met = True
        else:
            continue

        sleep(sleep_timeout)

    if not expectation_met:
        raise AssertionError(
            "Actual attribute value does not match "
            "expected for resource type '{}' with ID '{}'!" 
            "Expected: '{}' Actual: '{}'".format(resource_type,
                                                 str(resource_id),
                                                 expected_value,
                                                 resource[attribute_name])
        )


def assert_resource_exists_by_id(run_on_host, resource_type, resource_id):
    """Assert that a given resource exists within the OpenStack infrastructure.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.
        resource_id (uuid.UUID): The name of the OpenStack object to query for.

    Returns:
        list: OpenStack object instances parsed from JSON. [{str:obj}]

    Raises:
        AssertionError: No resources of the given type found!
    """

    __tracebackhide__ = True

    try:
        get_resource_by_id(run_on_host, resource_type, resource_id)
    except RuntimeError as e:
        raise AssertionError(str(e))


def assert_resource_exists_by_name(run_on_host, resource_type, resource_name):
    """Assert that a given resource exists within the OpenStack infrastructure.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.
        resource_name (str): The name of the OpenStack object to query for.

    Returns:
        list: OpenStack object instances parsed from JSON. [{str:obj}]

    Raises:
        AssertionError: No resources of the given type found!
    """

    __tracebackhide__ = True

    assert_msg = ("Resource type '{}' with name '{}' was "
                  "not found!".format(resource_type,  resource_name))

    assert (get_resources_by_name(run_on_host, resource_type, resource_name),
            assert_msg)


def create_bootable_volume(run_on_host, size, imageref, name, zone):
    """Create a bootable volume using a json file.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        size (int): Size of the volume.
        imageref (str): Reference ID for the image to apply to the new volume.
        name (str): Human readable name to apply to the volume.
        zone (str): The zone to apply to the new volume.

    Returns:
        uuid.UUID: The ID of the created resource.

    Raises:
        AssertionError: Failed to create bootable volume!
    """

    __tracebackhide__ = True

    cmd = (". ~/openrc ; "
           "openstack volume create "
           "-f json "
           "--size {} "
           "--image {} "
           "--availability-zone {} "
           "--bootable {}".format(size, imageref, zone, name))

    output = run_on_container(run_on_host, cmd, 'utility')
    assert_msg = 'Failed to create bootable volume!'

    try:
        result = json.loads(output.stdout)
    except ValueError:
        result = output.stdout

    assert type(result) is dict, assert_msg
    assert 'id' in result, assert_msg

    return uuid.UUID(result['id'])


# TODO: Should this also return the UUID of the resource?
def create_floating_ip(run_on_host, network_resource_id):
    """Create floating IP on a network

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.
        network_resource_id (uuid.UUID): The name of the OpenStack network
            object on which to create the floating IP.

    Returns:
        str: The newly created floating ip name

    Raises:
        AssertionError: Failed to create floating IP!
    """

    __tracebackhide__ = True

    cmd = (". ~/openrc ; openstack floating ip create "
           "-f json {}".format(str(network_resource_id)))
    key = 'floating_ip_address'
    output = run_on_container(run_on_host, cmd, 'utility')
    assert_msg = 'Failed to create floating IP!'

    assert (output.rc == 0), assert_msg

    try:
        result = json.loads(output.stdout)
    except ValueError:
        result = output.stdout

    assert type(result) is dict, assert_msg
    assert key in result.keys(), assert_msg

    return result[key]


def create_instance(run_on_host,
                    instance_name,
                    image_source_name,
                    image_name,
                    flavor_name,
                    network_name):
    """Create an instance from source (a glance image or a snapshot)

    Args:
        run_on_host (testinfra.host.Host): A hostname where the command is being
            executed.
        instance_name (str): Human readable name of instance.
        image_source_name (str): The OpenStack resource name of the image
            source.
        image_name (str): The OpenStack resource name of the image to use for
            provisioning the instance.
        flavor_name (str): The flavor to apply to the instance.
        network_name (str): The network attached to the newly created instance.

    Returns:
        uuid.UUID: The ID of the newly created instance.

    Raises:
        AssertionError: Failed to create instance!

    Example:
        `openstack server create --image <image_id> flavor <flavor> \
        --nic <net-id=network_id> server/instance_name` \
        `openstack server create --snapshot <snapshot_id> flavor <flavor> \
        --nic <net-id=network_id> server/instance_name`
    """

    __tracebackhide__ = True

    source_id = get_id_by_name(run_on_host, image_source_name, image_name)
    network_id = get_id_by_name(run_on_host, 'network', network_name)

    cmd = (". ~/openrc ; "
           "openstack server create "
           "-f json "
           "--{} {} "
           "--flavor {} "
           "--nic net-id={} {}".format(image_source_name,
                                       str(source_id),
                                       flavor_name,
                                       str(network_id),
                                       instance_name))

    output = run_on_container(run_on_host, cmd, 'utility')
    assert_msg = 'Failed to create instance!'

    try:
        result = json.loads(output.stdout)
    except ValueError:
        result = output.stdout

    assert type(result) is dict, assert_msg
    assert 'id' in result, assert_msg

    return uuid.UUID(result['id'])


def create_snapshot_from_instance(run_on_host, snapshot_name, instance_id):
    """Create snapshot on an instance

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.
        snapshot_name (str): The name of the newly created snapshot.
        instance_id (uuid.UUID): The name of the OpenStack instance from which
            the snapshot is created.

    Returns:
        uuid.UUID: The ID of the newly created snapshot.

    Raises:
        AssertionError: Failed to create snapshot!
    """

    __tracebackhide__ = True

    cmd = (". ~/openrc ; "
           "openstack server image create "
           "-f json "
           "--name {} {}".format(snapshot_name, instance_id))

    output = run_on_container(run_on_host, cmd, 'utility')
    assert_msg = 'Failed to create snapshot!'

    try:
        result = json.loads(output.stdout)
    except ValueError:
        result = output.stdout

    assert type(result) is dict, assert_msg
    assert 'id' in result, assert_msg

    return uuid.UUID(result['id'])


def delete_instance(run_on_host, instance_id):
    """Delete OpenStack instance

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.
        instance_id (uuid.UUID): The OpenStack resource ID of the instance to
            delete.

    Raises:
        AssertionError: Failed to delete resource!
    """

    __tracebackhide__ = True

    _delete_it(run_on_host, 'server', instance_id)


def delete_volume(run_on_host, volume_id, addl_flags=''):
    """Delete OpenStack volume

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.
        volume_id (uuid.UUID): OpenStack volume identifier (name or id).
        addl_flags (str): Add additional flags to the call to OpenStack CLI
            when deleting a volume.

    Raises:
        AssertionError: Failed to delete resource!
    """

    __tracebackhide__ = True

    _delete_it(run_on_host, 'volume', volume_id, addl_flags=addl_flags)


def generate_random_string(string_length=10):
    """Generate a random string of specified length string_length.

    Args:
        string_length (int): Size of string to generate.

    Returns:
        str: Random string of specified length (maximum of 32 characters)
    """

    random_str = str(uuid.uuid4())
    random_str = random_str.upper()
    random_str = random_str.replace("-", "")

    return random_str[0:string_length]  # Return the random_str string.


def get_id_by_name(run_on_host, resource_type, resource_name):
    """Get the ID associated with resource name of the given resource type.

    Note: If multiple resources of the same type share the same name then this
    function will return the ID for the first resource name match.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.
        resource_name (str): The name of the OpenStack resource instance to
            query for.

    Returns:
        uuid.UUID: ID of Openstack object instance.

    Raises:
        AssertionError: Resource type with given name not found!
    """

    __tracebackhide__ = True

    resources = get_resources_by_name(run_on_host, resource_type, resource_name)
    assert_msg = ("Resource type '{}' with given name '{}' was "
                  "not found!".format(resource_type, resource_name))

    if not resources:
        raise AssertionError(assert_msg)
    elif 'ID' in resources[0].keys():
        return uuid.UUID(resources[0]['ID'])
    else:
        raise AssertionError(assert_msg)


def get_osa_version(branch):
    """Get OpenStack version (code_name, major_version)

    This data is based on the git branch of the test suite being executed

    Args:
        branch (str): The rpc-openstack branch to query for.

    Returns:
        tuple of (str, str): (code_name, major_version) OpenStack version.

    Raises:
        AssertionError: Unknown RPC-O release detected!
    """

    __tracebackhide__ = True

    if branch in ['newton', 'newton-rc']:
        return 'Newton', '14'
    elif branch in ['pike', 'pike-rc']:
        return 'Pike', '16'
    elif branch in ['queens', 'queens-rc']:
        return 'Queens', '17'
    elif branch in ['rocky', 'rocky-rc']:
        return 'Rocky', '18'
    else:
        raise AssertionError('Unknown RPC-O release detected!')


def get_resource_by_id(run_on_host, resource_type, resource_id):
    """Retrieve the OpenStack resource that matches the specified unique ID and
    resource type.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.
        resource_id (uuid.UUID): The ID of the OpenStack resource instance to
            query for.

    Returns:
        dict: An OpenStack resource for the given resource ID. {str:obj}

    Raises:
        RuntimeError: Failed to find resource of given type with specified ID or
            somehow there are more than one resource with the same ID!
    """

    resources = get_resources_by_type(run_on_host, resource_type)

    try:
        matches = [x for x in resources if x['ID'] == resource_id]
    except (KeyError, TypeError):
        matches = []

    if not matches:
        raise RuntimeError("Resource type '{}' with ID '{}' was "
                           "not found!".format(resource_type, str(resource_id)))
    elif len(matches) > 1:
        raise RuntimeError("Multiple resources type ID '{}' were "
                           "found!".format(resource_type, str(resource_id)))

    return matches[0]


def get_resources_by_name(run_on_host, resource_type, resource_name):
    """Retrieve a list of OpenStack resources that match the desired resource
    name and type.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.
        resource_name (str): The name of the OpenStack resource instance to
            query for.

    Returns:
        list: A list of OpenStack resources that match the given criteria.
            [{str:obj}]
    """

    resources = get_resources_by_type(run_on_host, resource_type)

    try:
        matches = [x for x in resources if x['Name'] == resource_name]
    except (KeyError, TypeError):
        try:
            matches = [x for x in resources if x['Display Name']
                       == resource_name]
        except (KeyError, TypeError):
            matches = []

    if not matches:
        matches = []

    return matches


def get_resources_by_type(run_on_host, resource_type):
    """Retrieve a list of resources by OpenStack resource type.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action upon.
        resource_type (str): The OpenStack resource type to query for.

    Returns:
        list: A list of OpenStack resources of the given type. [{str:obj}]
    """

    cmd = (". ~/openrc ; openstack {} list -f json".format(resource_type))
    output = run_on_container(cmd, 'utility', run_on_host)

    try:
        result = json.loads(output.stdout)
    except ValueError:
        result = []

    return result


def parse_swift_recon(recon_out):
    """Parse swift-recon output into list of lists grouped by the content of
    the delimited blocks.

    Args:
        recon_out (str): CLI output from the `swift-recon` command.

    Returns:
        list: List of lists grouped by the content of the delimited blocks

    Example output from `swift-recon --md5` to be parsed:
    ============================================================================
    --> Starting reconnaissance on 3 hosts (object)
    ============================================================================
    [2018-07-19 15:36:40] Checking ring md5sums
    3/3 hosts matched, 0 error[s] while checking hosts.
    ============================================================================
    [2018-07-19 15:36:40] Checking swift.conf md5sum
    3/3 hosts matched, 0 error[s] while checking hosts.
    ============================================================================
    """

    lines = recon_out.splitlines()
    delimiter_regex = re.compile(r'^={79}')
    collection = []

    delimiter_positions = [ind for ind, x in enumerate(lines)
                           if delimiter_regex.match(x)]

    for ind, delimiter_position in enumerate(delimiter_positions):
        if ind != len(delimiter_positions) - 1:  # Are in the last position?
            start = delimiter_position + 1
            end = delimiter_positions[ind + 1]
            collection.append(lines[start:end])
    return collection


def parse_swift_ring_builder(ring_builder_output):
    """Parse the supplied output into a dictionary of swift ring data.

    Args:
        ring_builder_output (str): The output from the swift-ring-builder
                                   command.
    Returns:
        dict: Swift ring data. Empty dictionary if parse fails. {str: float}

    Example data:
        {'zones': 1.0,
         'replicas': 3.0,
         'devices': 9.0,
         'regions': 1.0,
         'dispersion': 0.0,
         'balance': 0.78,
         'partitions': 256.0}
    """

    swift_data = {}
    swift_lines = ring_builder_output.split('\n')
    matching = [s for s in swift_lines if "partitions" and "dispersion" in s]
    if matching:
        elements = [s.strip() for s in matching[0].split(',')]
        for element in elements:
            v, k = element.split(' ')
            swift_data[k] = float(v)

    return swift_data


def parse_table(ascii_table):
    """Parse an OpenStack ascii table

    Args:
        ascii_table (str): OpenStack ascii table.

    Returns:
        list of str: Column headers from table.
        list of str: Rows from table.
    """

    header = []
    data = []
    for line in filter(None, ascii_table.split('\n')):
        if '-+-' in line:
            continue
        if not header:
            header = list(filter(lambda x: x != '|', line.split()))
            continue
        data_row = []
        splitted_line = list(filter(lambda x: x != '|', line.split()))
        for i in range(len(splitted_line)):
            data_row.append(splitted_line[i])
        while len(data_row) < len(header):
            data_row.append('')
        data.append(data_row)
    return header, data


# TODO: What is the specific use case for pinging from utility container?
# TODO: Is no specific use case identified, then this helper is not needed.
def ping_ip_from_utility_container(ip, run_on_host):
    """Verify the IP address can be pinged from utility container on a host

    Args:
        ip (str): The string of the pinged IP address
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.

    Returns:
        bool: Whether the IP address can be pinged or not
    """

    cmd = "ping -c1 {}".format(ip)
    if run_on_container(run_on_host, cmd, 'utility').rc == 0:
        return True
    else:
        return False


def run_on_container(run_on_host, command, container_type):
    """Run the given command on the given container.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            wrapped command on.
        command (str): The bash command to run.
        container_type (str): The container type to run the command on.

    Returns:
        testinfra.CommandResult: Result of command execution.
    """

    pre_command = ("lxc-attach "
                   "-n $(lxc-ls -1 | grep {} | head -n 1) "
                   "-- bash -c".format(container_type))
    cmd = "{} '{}'".format(pre_command, command)

    return run_on_host.run(cmd)


def run_on_swift(run_on_host, cmd):
    """Run the given command on the swift container.

    Args:
        run_on_host (testinfra.Host): Testinfra host object to execute the
            wrapped command on.
        cmd (str): Command

    Returns:
        testinfra.CommandResult: Result of command execution.
    """

    command = (". ~/openrc ; "
               ". /openstack/venvs/swift-*/bin/activate ; "
               "{}".format(cmd))

    return run_on_container(run_on_host, command, 'swift')


def stop_server_instance(instance_id, run_on_host):
    """Stop an OpenStack server/instance

    Args:
        instance_id (uuid.UUID): The OpenStack resource ID for the instance
            to be stopped.
        run_on_host (testinfra.Host): Testinfra host object to execute the
            action on.

    Raises:
        AssertionError: Failed to stop instance!
    """

    __tracebackhide__ = True

    cmd = (". ~/openrc ; openstack server stop {}".format(instance_id))
    assert_msg = ("Failed to stop instance with resource"
                  "ID '{}'!".format(instance_id))

    assert run_on_container(run_on_host, cmd, 'utility').rc == 0, assert_msg
