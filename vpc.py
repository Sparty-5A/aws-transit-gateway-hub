"""
VPC module for AWS Cloud Networking Lab.

Provides functions to create and configure AWS VPCs with best practices.
"""

from typing import Optional

import pulumi_aws as aws

import pulumi


def create_vpc(
    name: str,
    cidr_block: str,
    enable_dns_hostnames: bool = True,
    enable_dns_support: bool = True,
    tags: Optional[dict] = None,
) -> aws.ec2.Vpc:
    """
    Create an AWS VPC with specified configuration.

    Args:
        name: Resource name for the VPC
        cidr_block: CIDR block for the VPC (e.g., "10.0.0.0/16")
        enable_dns_hostnames: Enable DNS hostnames in the VPC
        enable_dns_support: Enable DNS support in the VPC
        tags: Additional tags to apply to the VPC

    Returns:
        aws.ec2.Vpc: The created VPC resource

    Example:
        >>> vpc = create_vpc(
        ...     name="my-vpc",
        ...     cidr_block="10.0.0.0/16",
        ...     tags={"Environment": "dev"}
        ... )
    """
    if tags is None:
        tags = {}

    # Validate CIDR block (basic validation)
    if not cidr_block or "/" not in cidr_block:
        raise ValueError(f"Invalid CIDR block: {cidr_block}")

    vpc = aws.ec2.Vpc(
        name,
        cidr_block=cidr_block,
        enable_dns_hostnames=enable_dns_hostnames,
        enable_dns_support=enable_dns_support,
        tags={"Name": name, **tags},
    )

    # Log VPC creation
    pulumi.log.info(f"Creating VPC: {name} with CIDR {cidr_block}")

    return vpc


def get_vpc_by_id(vpc_id: str) -> aws.ec2.Vpc:
    """
    Get an existing VPC by ID.

    Args:
        vpc_id: The VPC ID to look up

    Returns:
        aws.ec2.Vpc: The VPC resource
    """
    return aws.ec2.Vpc.get("existing-vpc", vpc_id)


def create_vpc_endpoint(
    name: str,
    vpc_id: pulumi.Input[str],
    service_name: str,
    route_table_ids: Optional[list] = None,
    tags: Optional[dict] = None,
) -> aws.ec2.VpcEndpoint:
    """
    Create a VPC endpoint for AWS services.

    Useful for private connectivity to S3, DynamoDB, etc.

    Args:
        name: Resource name for the VPC endpoint
        vpc_id: VPC ID where endpoint will be created
        service_name: AWS service name (e.g., "com.amazonaws.us-east-1.s3")
        route_table_ids: Route tables to associate with the endpoint
        tags: Additional tags

    Returns:
        aws.ec2.VpcEndpoint: The created VPC endpoint

    Example:
        >>> # Create S3 endpoint for private S3 access
        >>> s3_endpoint = create_vpc_endpoint(
        ...     name="s3-endpoint",
        ...     vpc_id=vpc.id,
        ...     service_name="com.amazonaws.us-east-1.s3",
        ...     route_table_ids=[route_table.id]
        ... )
    """
    if tags is None:
        tags = {}

    if route_table_ids is None:
        route_table_ids = []

    endpoint = aws.ec2.VpcEndpoint(
        name,
        vpc_id=vpc_id,
        service_name=service_name,
        route_table_ids=route_table_ids,
        tags={"Name": name, **tags},
    )

    return endpoint


def enable_vpc_flow_logs(
    name: str,
    vpc_id: pulumi.Input[str],
    log_destination_type: str = "cloud-watch-logs",
    log_group_name: Optional[str] = None,
    traffic_type: str = "ALL",
    tags: Optional[dict] = None,
) -> aws.ec2.FlowLog:
    """
    Enable VPC Flow Logs for network monitoring.

    Args:
        name: Resource name for the flow log
        vpc_id: VPC ID to monitor
        log_destination_type: "cloud-watch-logs" or "s3"
        log_group_name: CloudWatch log group name (if using CloudWatch)
        traffic_type: "ACCEPT", "REJECT", or "ALL"
        tags: Additional tags

    Returns:
        aws.ec2.FlowLog: The created flow log

    Example:
        >>> # Enable flow logs for security monitoring
        >>> flow_log = enable_vpc_flow_logs(
        ...     name="vpc-flow-log",
        ...     vpc_id=vpc.id,
        ...     traffic_type="ALL"
        ... )
    """
    if tags is None:
        tags = {}

    # Create CloudWatch log group if using CloudWatch
    if log_destination_type == "cloud-watch-logs":
        if not log_group_name:
            log_group_name = f"/aws/vpc/flowlogs/{name}"

        log_group = aws.cloudwatch.LogGroup(
            f"{name}-log-group",
            name=log_group_name,
            retention_in_days=7,  # Keep logs for 7 days (adjust as needed)
            tags=tags,
        )

        # Create IAM role for flow logs
        flow_log_role = aws.iam.Role(
            f"{name}-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "vpc-flow-logs.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            }""",
        )

        # Attach policy to role
        flow_log_policy = aws.iam.RolePolicy(
            f"{name}-policy",
            role=flow_log_role.id,
            policy=log_group.arn.apply(
                lambda arn: f"""{{
                    "Version": "2012-10-17",
                    "Statement": [{{
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:DescribeLogGroups",
                            "logs:DescribeLogStreams"
                        ],
                        "Resource": "{arn}"
                    }}]
                }}"""
            ),
        )

        # Create flow log
        flow_log = aws.ec2.FlowLog(
            name,
            vpc_id=vpc_id,
            traffic_type=traffic_type,
            log_destination_type=log_destination_type,
            log_destination=log_group.arn,
            iam_role_arn=flow_log_role.arn,
            tags={"Name": name, **tags},
        )
    else:
        # S3 destination (simpler, no IAM role needed)
        flow_log = aws.ec2.FlowLog(
            name,
            vpc_id=vpc_id,
            traffic_type=traffic_type,
            log_destination_type=log_destination_type,
            tags={"Name": name, **tags},
        )

    return flow_log


def create_dhcp_options(
    name: str,
    domain_name: Optional[str] = None,
    domain_name_servers: Optional[list] = None,
    ntp_servers: Optional[list] = None,
    tags: Optional[dict] = None,
) -> aws.ec2.VpcDhcpOptions:
    """
    Create DHCP options set for VPC.

    Useful for custom DNS and NTP configuration.

    Args:
        name: Resource name
        domain_name: Domain name for DHCP clients
        domain_name_servers: List of DNS servers
        ntp_servers: List of NTP servers
        tags: Additional tags

    Returns:
        aws.ec2.VpcDhcpOptions: The DHCP options set
    """
    if tags is None:
        tags = {}

    if domain_name_servers is None:
        domain_name_servers = ["AmazonProvidedDNS"]

    dhcp_options_args = {
        "domain_name": domain_name,
        "domain_name_servers": domain_name_servers,
        "tags": {"Name": name, **tags},
    }

    if ntp_servers:
        dhcp_options_args["ntp_servers"] = ntp_servers

    # Remove None values
    dhcp_options_args = {k: v for k, v in dhcp_options_args.items() if v is not None}

    dhcp_options = aws.ec2.VpcDhcpOptions(name, **dhcp_options_args)

    return dhcp_options


def associate_dhcp_options(
    name: str, vpc_id: pulumi.Input[str], dhcp_options_id: pulumi.Input[str]
) -> aws.ec2.VpcDhcpOptionsAssociation:
    """
    Associate DHCP options with a VPC.

    Args:
        name: Resource name
        vpc_id: VPC ID
        dhcp_options_id: DHCP options ID

    Returns:
        aws.ec2.VpcDhcpOptionsAssociation: The association
    """
    association = aws.ec2.VpcDhcpOptionsAssociation(
        name, vpc_id=vpc_id, dhcp_options_id=dhcp_options_id
    )

    return association
