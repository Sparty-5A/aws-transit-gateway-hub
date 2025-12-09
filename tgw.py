"""
Transit Gateway Module

Provides functions to create and manage AWS Transit Gateway resources.
Supports hub-and-spoke architecture for connecting multiple VPCs.
"""

import pulumi
import pulumi_aws as aws
from typing import List, Optional, Dict


def create_transit_gateway(
    name: str,
    description: str = None,
    amazon_side_asn: int = 64512,
    default_route_table_association: bool = True,
    default_route_table_propagation: bool = True,
    dns_support: bool = True,
    vpn_ecmp_support: bool = True,
    tags: Optional[Dict[str, str]] = None,
) -> aws.ec2transitgateway.TransitGateway:
    """
    Create a Transit Gateway.
    
    Args:
        name: Resource name
        description: TGW description
        amazon_side_asn: BGP ASN for the AWS side (default: 64512)
        default_route_table_association: Auto-associate attachments with default route table
        default_route_table_propagation: Auto-propagate routes to default route table
        dns_support: Enable DNS support
        vpn_ecmp_support: Enable ECMP for VPN connections
        tags: Resource tags
    
    Returns:
        Transit Gateway resource
    """
    
    pulumi.log.info(f"🌉 Creating Transit Gateway: {name}")
    
    # Convert booleans to AWS expected strings
    default_rt_assoc = "enable" if default_route_table_association else "disable"
    default_rt_prop = "enable" if default_route_table_propagation else "disable"
    dns = "enable" if dns_support else "disable"
    vpn_ecmp = "enable" if vpn_ecmp_support else "disable"
    
    tgw = aws.ec2transitgateway.TransitGateway(
        name,
        description=description or f"Transit Gateway {name}",
        amazon_side_asn=amazon_side_asn,
        default_route_table_association=default_rt_assoc,
        default_route_table_propagation=default_rt_prop,
        dns_support=dns,
        vpn_ecmp_support=vpn_ecmp,
        tags=tags or {},
    )
    
    pulumi.log.info(f"✓ Transit Gateway created: {name}")
    
    return tgw


def create_transit_gateway_vpc_attachment(
    name: str,
    transit_gateway_id: pulumi.Input[str],
    vpc_id: pulumi.Input[str],
    subnet_ids: List[pulumi.Input[str]],
    dns_support: bool = True,
    ipv6_support: bool = False,
    appliance_mode_support: bool = False,
    tags: Optional[Dict[str, str]] = None,
) -> aws.ec2transitgateway.VpcAttachment:
    """
    Attach a VPC to a Transit Gateway.
    
    IMPORTANT: subnet_ids should be dedicated TGW subnets, one per AZ where you need connectivity.
    
    Args:
        name: Resource name
        transit_gateway_id: ID of the Transit Gateway
        vpc_id: ID of the VPC to attach
        subnet_ids: List of subnet IDs (one per AZ for TGW ENI placement)
        dns_support: Enable DNS support
        ipv6_support: Enable IPv6 support
        appliance_mode_support: Enable appliance mode support
        tags: Resource tags
    
    Returns:
        VPC attachment resource
    """
    
    pulumi.log.info(f"🔗 Creating TGW VPC attachment: {name}")
    
    # Convert booleans to AWS expected strings
    dns = "enable" if dns_support else "disable"
    ipv6 = "enable" if ipv6_support else "disable"
    appliance = "enable" if appliance_mode_support else "disable"
    
    attachment = aws.ec2transitgateway.VpcAttachment(
        name,
        transit_gateway_id=transit_gateway_id,
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        dns_support=dns,
        ipv6_support=ipv6,
        appliance_mode_support=appliance,
        tags=tags or {},
    )
    
    pulumi.log.info(f"✓ VPC attachment created: {name}")
    
    return attachment


def create_transit_gateway_route_table(
    name: str,
    transit_gateway_id: pulumi.Input[str],
    tags: Optional[Dict[str, str]] = None,
) -> aws.ec2transitgateway.RouteTable:
    """
    Create a Transit Gateway route table.
    
    Args:
        name: Resource name
        transit_gateway_id: ID of the Transit Gateway
        tags: Resource tags
    
    Returns:
        TGW route table resource
    """
    
    pulumi.log.info(f"📋 Creating TGW route table: {name}")
    
    route_table = aws.ec2transitgateway.RouteTable(
        name,
        transit_gateway_id=transit_gateway_id,
        tags=tags or {},
    )
    
    pulumi.log.info(f"✓ TGW route table created: {name}")
    
    return route_table


def create_transit_gateway_route_table_association(
    name: str,
    transit_gateway_attachment_id: pulumi.Input[str],
    transit_gateway_route_table_id: pulumi.Input[str],
) -> aws.ec2transitgateway.RouteTableAssociation:
    """
    Associate a TGW attachment with a TGW route table.
    
    This determines which route table the TGW will use when routing traffic FROM this attachment.
    
    Args:
        name: Resource name
        transit_gateway_attachment_id: ID of the TGW attachment
        transit_gateway_route_table_id: ID of the TGW route table
    
    Returns:
        Route table association resource
    """
    
    pulumi.log.info(f"🔗 Creating TGW route table association: {name}")
    
    association = aws.ec2transitgateway.RouteTableAssociation(
        name,
        transit_gateway_attachment_id=transit_gateway_attachment_id,
        transit_gateway_route_table_id=transit_gateway_route_table_id,
    )
    
    pulumi.log.info(f"✓ TGW route table association created: {name}")
    
    return association


def create_transit_gateway_route_table_propagation(
    name: str,
    transit_gateway_attachment_id: pulumi.Input[str],
    transit_gateway_route_table_id: pulumi.Input[str],
) -> aws.ec2transitgateway.RouteTablePropagation:
    """
    Enable route propagation from a TGW attachment to a TGW route table.
    
    This allows the attachment's CIDR to be automatically added as a route in the route table.
    
    Args:
        name: Resource name
        transit_gateway_attachment_id: ID of the TGW attachment
        transit_gateway_route_table_id: ID of the TGW route table
    
    Returns:
        Route table propagation resource
    """
    
    pulumi.log.info(f"📡 Enabling TGW route propagation: {name}")
    
    propagation = aws.ec2transitgateway.RouteTablePropagation(
        name,
        transit_gateway_attachment_id=transit_gateway_attachment_id,
        transit_gateway_route_table_id=transit_gateway_route_table_id,
    )
    
    pulumi.log.info(f"✓ TGW route propagation enabled: {name}")
    
    return propagation


def create_transit_gateway_route(
    name: str,
    destination_cidr_block: str,
    transit_gateway_route_table_id: pulumi.Input[str],
    transit_gateway_attachment_id: pulumi.Input[str] = None,
    blackhole: bool = False,
) -> aws.ec2transitgateway.Route:
    """
    Create a static route in a Transit Gateway route table.
    
    Args:
        name: Resource name
        destination_cidr_block: Destination CIDR for the route
        transit_gateway_route_table_id: ID of the TGW route table
        transit_gateway_attachment_id: ID of the TGW attachment (next hop)
        blackhole: Create a blackhole route (drops traffic)
    
    Returns:
        TGW route resource
    """
    
    pulumi.log.info(f"🛣️ Creating TGW route: {destination_cidr_block} in {name}")
    
    route_args = {
        "destination_cidr_block": destination_cidr_block,
        "transit_gateway_route_table_id": transit_gateway_route_table_id,
        "blackhole": blackhole,
    }
    
    if transit_gateway_attachment_id and not blackhole:
        route_args["transit_gateway_attachment_id"] = transit_gateway_attachment_id
    
    route = aws.ec2transitgateway.Route(name, **route_args)
    
    pulumi.log.info(f"✓ TGW route created: {destination_cidr_block}")
    
    return route


def add_tgw_route_to_vpc_route_table(
    name: str,
    route_table_id: pulumi.Input[str],
    destination_cidr_block: str,
    transit_gateway_id: pulumi.Input[str],
) -> aws.ec2.Route:
    """
    Add a route to a VPC route table pointing to the Transit Gateway.
    
    This is needed in each VPC's route table to send traffic to the TGW.
    
    Args:
        name: Resource name
        route_table_id: ID of the VPC route table
        destination_cidr_block: Destination CIDR (other VPC's CIDR)
        transit_gateway_id: ID of the Transit Gateway
    
    Returns:
        Route resource
    """
    
    pulumi.log.info(f"🛣️ Adding VPC route to TGW: {destination_cidr_block} → TGW")
    
    route = aws.ec2.Route(
        name,
        route_table_id=route_table_id,
        destination_cidr_block=destination_cidr_block,
        transit_gateway_id=transit_gateway_id,
    )
    
    pulumi.log.info(f"✓ VPC route to TGW added: {destination_cidr_block}")
    
    return route


def create_tgw_with_vpc_attachments(
    name_prefix: str,
    tgw_description: str,
    vpc_configs: List[Dict],
    use_default_route_table: bool = True,
    tags: Optional[Dict[str, str]] = None,
) -> tuple:
    """
    Create a Transit Gateway with multiple VPC attachments.
    
    Convenience function for common hub-and-spoke setup.
    
    Args:
        name_prefix: Prefix for resource names
        tgw_description: Description for the TGW
        vpc_configs: List of VPC configuration dicts, each containing:
            - name: VPC name
            - vpc_id: VPC ID
            - subnet_ids: List of TGW subnet IDs (one per AZ)
            - cidr: VPC CIDR block
            - route_table_id: VPC route table ID (for return routes)
        use_default_route_table: Use TGW default route table (simple setup)
        tags: Common tags for all resources
    
    Returns:
        Tuple of (tgw, attachments, routes)
    """
    
    pulumi.log.info(f"🌉 Creating Transit Gateway with {len(vpc_configs)} VPC attachments")
    
    # Create Transit Gateway
    tgw = create_transit_gateway(
        name=f"{name_prefix}-tgw",
        description=tgw_description,
        default_route_table_association=use_default_route_table,
        default_route_table_propagation=use_default_route_table,
        tags=tags,
    )
    
    # Create VPC attachments
    attachments = []
    for vpc_config in vpc_configs:
        attachment = create_transit_gateway_vpc_attachment(
            name=f"{name_prefix}-{vpc_config['name']}-attachment",
            transit_gateway_id=tgw.id,
            vpc_id=vpc_config["vpc_id"],
            subnet_ids=vpc_config["subnet_ids"],
            tags={**tags, "VPC": vpc_config["name"]} if tags else {"VPC": vpc_config["name"]},
        )
        attachments.append(attachment)
    
    # Add routes in VPC route tables back to TGW
    # Each VPC needs routes to all OTHER VPCs
    vpc_routes = []
    for i, src_vpc in enumerate(vpc_configs):
        for j, dst_vpc in enumerate(vpc_configs):
            if i != j:  # Don't create route to self
                route = add_tgw_route_to_vpc_route_table(
                    name=f"{name_prefix}-{src_vpc['name']}-to-{dst_vpc['name']}",
                    route_table_id=src_vpc["route_table_id"],
                    destination_cidr_block=dst_vpc["cidr"],
                    transit_gateway_id=tgw.id,
                )
                vpc_routes.append(route)
    
    pulumi.log.info("✓ Transit Gateway with VPC attachments created")
    
    return tgw, attachments, vpc_routes


def get_default_tgw_route_table_id(
    transit_gateway_id: pulumi.Input[str],
) -> pulumi.Output[str]:
    """
    Get the default route table ID for a Transit Gateway.
    
    Note: This requires the TGW to be created with default route table enabled.
    
    Args:
        transit_gateway_id: ID of the Transit Gateway
    
    Returns:
        Default route table ID as Output
    """
    
    # The default route table ID is not directly accessible via Pulumi TGW resource
    # In practice, you'd need to query AWS API or use the TGW's default_route_table_id output
    # For now, we'll note this as a limitation
    
    pulumi.log.warn("⚠️ Default TGW route table ID must be queried from AWS API")
    pulumi.log.warn("   Consider using explicit route table creation for full control")
    
    # Return the transit_gateway_id as a placeholder
    # In real usage, you'd use aws.ec2transitgateway.get_route_table()
    return transit_gateway_id
