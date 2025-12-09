"""
Networking module for AWS Cloud.

Provides functions for subnets, route tables, gateways, and NAT.
"""

from typing import List, Optional, Tuple

import pulumi_aws as aws
import pulumi


def create_subnets(
    name_prefix: str,
    vpc_id: pulumi.Input[str],
    cidr_blocks: List[str],
    availability_zones: List[str],
    public: bool = False,
    tags: Optional[dict] = None,
) -> List[aws.ec2.Subnet]:
    """Create multiple subnets."""
    if tags is None:
        tags = {}

    subnets = []
    for i, (cidr, az) in enumerate(zip(cidr_blocks, availability_zones)):
        subnet = aws.ec2.Subnet(
            f"{name_prefix}-{i}",
            vpc_id=vpc_id,
            cidr_block=cidr,
            availability_zone=az,
            map_public_ip_on_launch=public,
            tags={"Name": f"{name_prefix}-{i}", **tags},
        )
        subnets.append(subnet)

    return subnets


def create_internet_gateway(
    name: str, vpc_id: pulumi.Input[str], tags: Optional[dict] = None
) -> aws.ec2.InternetGateway:
    """Create Internet Gateway for public subnets."""
    if tags is None:
        tags = {}

    igw = aws.ec2.InternetGateway(name, vpc_id=vpc_id, tags={"Name": name, **tags})
    pulumi.log.info(f"Creating Internet Gateway: {name}")
    return igw


def create_nat_gateway(
    name: str, subnet_id: pulumi.Input[str], tags: Optional[dict] = None
) -> Tuple[aws.ec2.NatGateway, aws.ec2.Eip]:
    """
    Create NAT Gateway and its Elastic IP.

    Returns a tuple of (NatGateway, Eip).
    """
    if tags is None:
        tags = {}

    # Allocate Elastic IP
    eip = aws.ec2.Eip(f"{name}-eip", tags={"Name": f"{name}-eip", **tags})
    # eip = aws.ec2.Eip(f"{name}-eip", vpc=True, tags={"Name": f"{name}-eip", **tags})

    # Create NAT Gateway
    nat_gateway = aws.ec2.NatGateway(
        name, subnet_id=subnet_id, allocation_id=eip.id, tags={"Name": name, **tags}
    )

    pulumi.log.info(f"Creating NAT Gateway: {name}")

    return nat_gateway, eip


def create_route_tables(
    name_prefix: str, vpc_id: pulumi.Input[str], count: int = 1, tags: Optional[dict] = None
) -> List[aws.ec2.RouteTable]:
    """Create route tables."""
    if tags is None:
        tags = {}

    route_tables = []
    for i in range(count):
        rt = aws.ec2.RouteTable(
            f"{name_prefix}-{i}", vpc_id=vpc_id, tags={"Name": f"{name_prefix}-{i}", **tags}
        )
        route_tables.append(rt)

    return route_tables


def create_route(
    name: str,
    route_table_id: pulumi.Input[str],
    destination_cidr_block: str,
    gateway_id: Optional[pulumi.Input[str]] = None,
    nat_gateway_id: Optional[pulumi.Input[str]] = None,
    vpc_peering_connection_id: Optional[pulumi.Input[str]] = None,
) -> aws.ec2.Route:
    """Create a route in a route table."""
    route_args = {
        "route_table_id": route_table_id,
        "destination_cidr_block": destination_cidr_block,
    }

    if gateway_id:
        route_args["gateway_id"] = gateway_id
    elif nat_gateway_id:
        route_args["nat_gateway_id"] = nat_gateway_id
    elif vpc_peering_connection_id:
        route_args["vpc_peering_connection_id"] = vpc_peering_connection_id
    else:
        raise ValueError("Must specify gateway_id, nat_gateway_id, or vpc_peering_connection_id")

    route = aws.ec2.Route(name, **route_args)
    return route


def associate_route_table(
    name: str, subnet_id: pulumi.Input[str], route_table_id: pulumi.Input[str]
) -> aws.ec2.RouteTableAssociation:
    """Associate route table with subnet."""
    association = aws.ec2.RouteTableAssociation(
        name, subnet_id=subnet_id, route_table_id=route_table_id
    )
    return association
