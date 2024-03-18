import netmiko
import re
from resources.routing_protocols.ospf.OSPFArea import OSPFArea
from resources.routing_protocols.ospf.OSPFInformation import OSPFInformation
from resources.routing_protocols.Network import Network
from resources.routing_protocols.Redistribution import Redistribution
from resources.cisco.getting_redistribution import get_routing_protocol_redistribution
from resources.cisco.getting_routing_protocol_information import (get_routing_protocol_distance,
                                                                  get_routing_protocol_default_information_originate,
                                                                  get_routing_protocol_default_metric_of_redistributed_routes)


def is_ospf_enabled(sh_run_sec_ospf_output: str) -> bool:
    pattern = r'(router ospf)'
    if re.search(pattern, sh_run_sec_ospf_output):
        return True
    return False


def get_ospf_process_id(sh_run_sec_ospf_output: str) -> int | None:
    pattern = r'(router ospf )\d*'
    match = re.search(pattern, sh_run_sec_ospf_output)
    if match:
        process_id = int(match.group()[len('router ospf '):])
        return process_id
    return None


def get_ospf_router_id(sh_ip_ospf_database_output: str) -> str | None:
    pattern = r'(OSPF Router with ID ).*(Pro)'
    match = re.search(pattern, sh_ip_ospf_database_output)
    if match:
        router_id = match.group()[len('OSPF Router with ID ') + 1:-len('  (Pro')]
        return router_id
    return None


def get_ospf_auto_cost_reference_bandwidth(sh_run_sec_ospf_output: str) -> int:
    pattern = r'(auto-cost reference-bandwidth )\d*'
    match = re.search(pattern, sh_run_sec_ospf_output)
    if match:
        auto_cost_reference_bandwidth = int(match.group()[len('auto-cost reference-bandwidth '):])
        return auto_cost_reference_bandwidth
    return 100


def get_ospf_maximum_paths(sh_run_sec_ospf_output: str) -> int:
    pattern = r'(maximum-paths )\d*'
    match = re.search(pattern, sh_run_sec_ospf_output)
    if match:
        maximum_paths = int(match.group()[len('maximum-paths '):])
        return maximum_paths
    return 4


def get_ospf_passive_interface_default(sh_run_sec_ospf_output: str) -> bool:
    pattern = r'(passive-interface default)'
    if re.search(pattern, sh_run_sec_ospf_output):
        return True
    return False


def get_ospf_area_ids(sh_ip_ospf_output: str) -> list[str] | None:
    pattern = r'(Area \d*)'
    match = re.findall(pattern, sh_ip_ospf_output)
    list_of_areas_id: list[str] = [m[5:] for m in match if len(m) > 5]
    if re.search(r'Area BACKBONE', sh_ip_ospf_output):
        list_of_areas_id.append('0')
    if len(list_of_areas_id) == 0:
        return None
    return list_of_areas_id


def get_ospf_area_authentication_message_digest(area_id: str, sh_run_sec_ospf_output: str) -> bool:
    pattern = f'(area {area_id} authentication message-digest)'
    if re.search(pattern, sh_run_sec_ospf_output):
        return True
    return False


def get_ospf_area_type(area_id: str, sh_run_sec_ospf_output: str) -> str:
    if re.search(f'(area {area_id} nssa)', sh_run_sec_ospf_output):
        return 'nssa'
    if re.search(f'(area {area_id} stub)', sh_run_sec_ospf_output):
        return 'stub'
    return 'standard'


def get_ospf_area_networks(area_id: str, sh_run_sec_ospf_output: str) -> dict[str, Network]:
    pattern = f'(network .* area {area_id})'
    match = re.findall(pattern, sh_run_sec_ospf_output)
    if not match:
        return {}

    list_of_networks: list[str] = [line[len('network '):-len(f' area {area_id}')] for line in match]

    networks: dict[str, Network] = {}
    for network in list_of_networks:
        network_name, wildcard = network.split(' ')
        networks[network] = Network(network=network_name,
                                    mask=None,
                                    wildcard=wildcard)
    return networks


def get_ospf_area_information(area_id: str, sh_run_sec_ospf_output: str) -> OSPFArea:
    is_authentication_message_digest: bool = get_ospf_area_authentication_message_digest(area_id, sh_run_sec_ospf_output)
    area_type: str = get_ospf_area_type(area_id, sh_run_sec_ospf_output)
    networks: dict[str, Network] = get_ospf_area_networks(area_id, sh_run_sec_ospf_output)

    area_info = OSPFArea(id=area_id,
                         is_authentication_message_digest=is_authentication_message_digest,
                         type=area_type,
                         networks=networks)
    return area_info


def get_ospf_information(connection: netmiko.BaseConnection) -> OSPFInformation | None:
    connection.enable()
    sh_run_sec_ospf_output: str = connection.send_command("show run | sec ospf")
    sh_ip_ospf_database_output: str = connection.send_command("show ip ospf database")
    sh_ip_ospf_output: str = connection.send_command("show ip ospf")
    connection.exit_enable_mode()

    if not is_ospf_enabled(sh_run_sec_ospf_output):
        return None

    process_id: int = get_ospf_process_id(sh_run_sec_ospf_output)
    router_id: str = get_ospf_router_id(sh_ip_ospf_database_output)
    auto_cost_reference_bandwidth: int = get_ospf_auto_cost_reference_bandwidth(sh_run_sec_ospf_output)
    default_information_originate: bool = get_routing_protocol_default_information_originate(sh_run_sec_ospf_output)
    default_metric_of_redistributed_routes: int = (
        get_routing_protocol_default_metric_of_redistributed_routes('ospf', sh_run_sec_ospf_output))
    distance: int = get_routing_protocol_distance('ospf', sh_run_sec_ospf_output)
    maximum_paths: int = get_ospf_maximum_paths(sh_run_sec_ospf_output)
    passive_interface_default: bool = get_ospf_passive_interface_default(sh_run_sec_ospf_output)
    redistribution: Redistribution = get_routing_protocol_redistribution(sh_run_sec_ospf_output)

    list_of_areas_id = get_ospf_area_ids(sh_ip_ospf_output)
    areas: dict[str, OSPFArea] = {}
    for area_id in list_of_areas_id:
        areas[area_id] = get_ospf_area_information(area_id, sh_run_sec_ospf_output)

    ospf_info = OSPFInformation(process_id=process_id,
                                router_id=router_id,
                                auto_cost_reference_bandwidth=auto_cost_reference_bandwidth,
                                default_information_originate=default_information_originate,
                                default_metric_of_redistributed_routes=default_metric_of_redistributed_routes,
                                distance=distance,
                                maximum_paths=maximum_paths,
                                passive_interface_default=passive_interface_default,
                                redistribution=redistribution,
                                areas=areas)
    return ospf_info
