"""
AWS Transit Gateway Tutorial (Tutorial 6)

Creates two VPCs connected via Transit Gateway in hub-and-spoke model.

Architecture:
- Lab VPC (10.200.0.0/16) with dedicated TGW subnets
- Dev VPC (10.201.0.0/16) with dedicated TGW subnets  
- Transit Gateway (central hub)
- TGW attachments for both VPCs
- Automatic route propagation
- Test instances in each VPC

Based on: https://www.packetswitch.co.uk/aws-transit-gateway-introduction/
"""

import pulumi
import pulumi_aws as aws

# Import custom modules
from vpc import create_vpc
from networking import (
    create_subnets,
    create_internet_gateway,
    create_route_tables,
    create_route,
    associate_route_table,
)
from tgw import (
    create_transit_gateway,
    create_transit_gateway_vpc_attachment,
    add_tgw_route_to_vpc_route_table,
)

# ==========================================
# Configuration
# ==========================================

config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

# VPC CIDRs (must not overlap!)
lab_vpc_cidr = config.get("lab_vpc_cidr") or "10.200.0.0/16"
lab_subnet_cidr = config.get("lab_subnet_cidr") or "10.200.10.0/24"
lab_tgw_subnet_a_cidr = config.get("lab_tgw_subnet_a_cidr") or "10.200.255.0/24"
lab_tgw_subnet_b_cidr = config.get("lab_tgw_subnet_b_cidr") or "10.200.254.0/24"

dev_vpc_cidr = config.get("dev_vpc_cidr") or "10.201.0.0/16"
dev_subnet_cidr = config.get("dev_subnet_cidr") or "10.201.10.0/24"
dev_tgw_subnet_a_cidr = config.get("dev_tgw_subnet_a_cidr") or "10.201.255.0/24"
dev_tgw_subnet_b_cidr = config.get("dev_tgw_subnet_b_cidr") or "10.201.254.0/24"

# Instance configuration
instance_type = config.get("instance_type") or "t3.micro"
key_name = config.get("key_name")  # Optional SSH key

# Transit Gateway configuration
tgw_amazon_side_asn = config.get_int("tgw_asn") or 64512
use_default_tgw_route_table = config.get_bool("tgw_use_default_rt") or True

# Region
aws_region = config.get("aws:region") or "us-east-1"

# Common tags
common_tags = {
    "Project": project_name,
    "ManagedBy": "Pulumi",
    "Environment": stack_name,
    "Tutorial": "6-Transit-Gateway",
}

pulumi.log.info(f"🚀 Deploying Transit Gateway Tutorial")
pulumi.log.info(f"   Lab VPC: {lab_vpc_cidr}")
pulumi.log.info(f"   Dev VPC: {dev_vpc_cidr}")
pulumi.log.info(f"   TGW ASN: {tgw_amazon_side_asn}")
pulumi.log.info(f"   Region: {aws_region}")

# ==========================================
# Get Latest Amazon Linux 2023 AMI
# ==========================================

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        {"name": "name", "values": ["al2023-ami-*-x86_64"]},
        {"name": "virtualization-type", "values": ["hvm"]},
    ],
)

# ==========================================
# Lab VPC (10.200.0.0/16)
# ==========================================

pulumi.log.info("📦 Creating Lab VPC")

# VPC
lab_vpc = create_vpc(
    name=f"{project_name}-lab-vpc",
    cidr_block=lab_vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"lab-vpc-{stack_name}"},
)

# Workload Subnet (for test instance)
lab_workload_subnets = create_subnets(
    name_prefix=f"{project_name}-lab-workload",
    vpc_id=lab_vpc.id,
    cidr_blocks=[lab_subnet_cidr],
    availability_zones=[f"{aws_region}a"],
    public=False,  # Private subnet (will route through TGW)
    tags={**common_tags, "Name": f"lab-workload-subnet-{stack_name}", "Type": "Workload"},
)
lab_workload_subnet = lab_workload_subnets[0]

# TGW Subnets (dedicated for Transit Gateway ENIs)
lab_tgw_subnets = create_subnets(
    name_prefix=f"{project_name}-lab-tgw",
    vpc_id=lab_vpc.id,
    cidr_blocks=[lab_tgw_subnet_a_cidr, lab_tgw_subnet_b_cidr],
    availability_zones=[f"{aws_region}a", f"{aws_region}b"],
    public=False,  # TGW subnets are always private
    tags={**common_tags, "Type": "TransitGateway"},
)
lab_tgw_subnet_a = lab_tgw_subnets[0]
lab_tgw_subnet_b = lab_tgw_subnets[1]

# Internet Gateway (for initial SSH access)
lab_igw = create_internet_gateway(
    name=f"{project_name}-lab-igw",
    vpc_id=lab_vpc.id,
    tags={**common_tags, "Name": f"lab-igw-{stack_name}"},
)

# Route Table for Workload Subnet
lab_route_tables = create_route_tables(
    name_prefix=f"{project_name}-lab-workload",
    vpc_id=lab_vpc.id,
    count=1,
    tags={**common_tags, "Name": f"lab-workload-rt-{stack_name}"},
)
lab_route_table = lab_route_tables[0]

# Route to Internet (for updates, SSH)
lab_igw_route = create_route(
    name=f"{project_name}-lab-igw-route",
    route_table_id=lab_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=lab_igw.id,
)

# Associate route table with workload subnet
lab_rta = associate_route_table(
    name=f"{project_name}-lab-workload-rta",
    subnet_id=lab_workload_subnet.id,
    route_table_id=lab_route_table.id,
)

pulumi.log.info("✓ Lab VPC created")

# ==========================================
# Dev VPC (10.201.0.0/16)
# ==========================================

pulumi.log.info("📦 Creating Dev VPC")

# VPC
dev_vpc = create_vpc(
    name=f"{project_name}-dev-vpc",
    cidr_block=dev_vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"dev-vpc-{stack_name}"},
)

# Workload Subnet (for test instance)
dev_workload_subnets = create_subnets(
    name_prefix=f"{project_name}-dev-workload",
    vpc_id=dev_vpc.id,
    cidr_blocks=[dev_subnet_cidr],
    availability_zones=[f"{aws_region}a"],
    public=False,  # Private subnet (will route through TGW)
    tags={**common_tags, "Name": f"dev-workload-subnet-{stack_name}", "Type": "Workload"},
)
dev_workload_subnet = dev_workload_subnets[0]

# TGW Subnets (dedicated for Transit Gateway ENIs)
dev_tgw_subnets = create_subnets(
    name_prefix=f"{project_name}-dev-tgw",
    vpc_id=dev_vpc.id,
    cidr_blocks=[dev_tgw_subnet_a_cidr, dev_tgw_subnet_b_cidr],
    availability_zones=[f"{aws_region}a", f"{aws_region}b"],
    public=False,  # TGW subnets are always private
    tags={**common_tags, "Type": "TransitGateway"},
)
dev_tgw_subnet_a = dev_tgw_subnets[0]
dev_tgw_subnet_b = dev_tgw_subnets[1]

# Internet Gateway (for initial SSH access)
dev_igw = create_internet_gateway(
    name=f"{project_name}-dev-igw",
    vpc_id=dev_vpc.id,
    tags={**common_tags, "Name": f"dev-igw-{stack_name}"},
)

# Route Table for Workload Subnet
dev_route_tables = create_route_tables(
    name_prefix=f"{project_name}-dev-workload",
    vpc_id=dev_vpc.id,
    count=1,
    tags={**common_tags, "Name": f"dev-workload-rt-{stack_name}"},
)
dev_route_table = dev_route_tables[0]

# Route to Internet (for updates, SSH)
dev_igw_route = create_route(
    name=f"{project_name}-dev-igw-route",
    route_table_id=dev_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=dev_igw.id,
)

# Associate route table with workload subnet
dev_rta = associate_route_table(
    name=f"{project_name}-dev-workload-rta",
    subnet_id=dev_workload_subnet.id,
    route_table_id=dev_route_table.id,
)

pulumi.log.info("✓ Dev VPC created")

# ==========================================
# Transit Gateway
# ==========================================

pulumi.log.info("🌉 Creating Transit Gateway")

# Create Transit Gateway
tgw = create_transit_gateway(
    name=f"{project_name}-tgw",
    description=f"Transit Gateway for {project_name}",
    amazon_side_asn=tgw_amazon_side_asn,
    default_route_table_association=use_default_tgw_route_table,
    default_route_table_propagation=use_default_tgw_route_table,
    dns_support=True,
    vpn_ecmp_support=True,
    tags={**common_tags, "Name": f"tgw-{stack_name}"},
)

pulumi.log.info("✓ Transit Gateway created")

# ==========================================
# Transit Gateway Attachments
# ==========================================

pulumi.log.info("🔗 Creating TGW Attachments")

# Lab VPC Attachment
lab_attachment = create_transit_gateway_vpc_attachment(
    name=f"{project_name}-lab-tgw-attachment",
    transit_gateway_id=tgw.id,
    vpc_id=lab_vpc.id,
    subnet_ids=[lab_tgw_subnet_a.id, lab_tgw_subnet_b.id],  # One per AZ
    dns_support=True,
    tags={**common_tags, "Name": f"lab-tgw-attachment-{stack_name}", "VPC": "lab"},
)

# Dev VPC Attachment
dev_attachment = create_transit_gateway_vpc_attachment(
    name=f"{project_name}-dev-tgw-attachment",
    transit_gateway_id=tgw.id,
    vpc_id=dev_vpc.id,
    subnet_ids=[dev_tgw_subnet_a.id, dev_tgw_subnet_b.id],  # One per AZ
    dns_support=True,
    tags={**common_tags, "Name": f"dev-tgw-attachment-{stack_name}", "VPC": "dev"},
)

pulumi.log.info("✓ TGW Attachments created")

# ==========================================
# VPC Route Table Updates
# ==========================================

pulumi.log.info("🛣️ Adding TGW routes to VPC route tables")

# Lab VPC: Route to Dev VPC via TGW
lab_to_dev_route = add_tgw_route_to_vpc_route_table(
    name=f"{project_name}-lab-to-dev-via-tgw",
    route_table_id=lab_route_table.id,
    destination_cidr_block=dev_vpc_cidr,
    transit_gateway_id=tgw.id,
)

# Dev VPC: Route to Lab VPC via TGW
dev_to_lab_route = add_tgw_route_to_vpc_route_table(
    name=f"{project_name}-dev-to-lab-via-tgw",
    route_table_id=dev_route_table.id,
    destination_cidr_block=lab_vpc_cidr,
    transit_gateway_id=tgw.id,
)

pulumi.log.info("✓ VPC routes to TGW added")

# ==========================================
# Security Groups
# ==========================================

pulumi.log.info("🔒 Creating Security Groups")

# Lab VPC Security Group
lab_sg = aws.ec2.SecurityGroup(
    f"{project_name}-lab-sg",
    vpc_id=lab_vpc.id,
    description="Security group for Lab VPC test instance",
    ingress=[
        # SSH from anywhere (for testing)
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "SSH access",
        },
        # ICMP from Dev VPC (for ping tests)
        {
            "protocol": "icmp",
            "from_port": -1,
            "to_port": -1,
            "cidr_blocks": [dev_vpc_cidr],
            "description": "ICMP from Dev VPC",
        },
        # All traffic from Dev VPC (for testing)
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": [dev_vpc_cidr],
            "description": "All traffic from Dev VPC",
        },
    ],
    egress=[
        # Allow all outbound
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound",
        },
    ],
    tags={**common_tags, "Name": f"lab-sg-{stack_name}"},
)

# Dev VPC Security Group
dev_sg = aws.ec2.SecurityGroup(
    f"{project_name}-dev-sg",
    vpc_id=dev_vpc.id,
    description="Security group for Dev VPC test instance",
    ingress=[
        # SSH from anywhere (for testing)
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "SSH access",
        },
        # ICMP from Lab VPC (for ping tests)
        {
            "protocol": "icmp",
            "from_port": -1,
            "to_port": -1,
            "cidr_blocks": [lab_vpc_cidr],
            "description": "ICMP from Lab VPC",
        },
        # All traffic from Lab VPC (for testing)
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": [lab_vpc_cidr],
            "description": "All traffic from Lab VPC",
        },
    ],
    egress=[
        # Allow all outbound
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Allow all outbound",
        },
    ],
    tags={**common_tags, "Name": f"dev-sg-{stack_name}"},
)

pulumi.log.info("✓ Security Groups created")

# ==========================================
# EC2 Test Instances
# ==========================================

pulumi.log.info("🖥️ Creating Test Instances")

# Lab VPC Test Instance
lab_instance = aws.ec2.Instance(
    f"{project_name}-lab-instance",
    instance_type=instance_type,
    ami=ami.id,
    subnet_id=lab_workload_subnet.id,
    vpc_security_group_ids=[lab_sg.id],
    associate_public_ip_address=True,  # For SSH access
    key_name=key_name,
    tags={**common_tags, "Name": f"lab-instance-{stack_name}"},
)

# Dev VPC Test Instance
dev_instance = aws.ec2.Instance(
    f"{project_name}-dev-instance",
    instance_type=instance_type,
    ami=ami.id,
    subnet_id=dev_workload_subnet.id,
    vpc_security_group_ids=[dev_sg.id],
    associate_public_ip_address=True,  # For SSH access
    key_name=key_name,
    tags={**common_tags, "Name": f"dev-instance-{stack_name}"},
)

pulumi.log.info("✓ Test Instances created")

# ==========================================
# Outputs
# ==========================================

# Lab VPC
pulumi.export("lab_vpc_id", lab_vpc.id)
pulumi.export("lab_vpc_cidr", lab_vpc_cidr)
pulumi.export("lab_workload_subnet_id", lab_workload_subnet.id)
pulumi.export("lab_tgw_subnet_a_id", lab_tgw_subnet_a.id)
pulumi.export("lab_tgw_subnet_b_id", lab_tgw_subnet_b.id)
pulumi.export("lab_instance_id", lab_instance.id)
pulumi.export("lab_instance_public_ip", lab_instance.public_ip)
pulumi.export("lab_instance_private_ip", lab_instance.private_ip)

# Dev VPC
pulumi.export("dev_vpc_id", dev_vpc.id)
pulumi.export("dev_vpc_cidr", dev_vpc_cidr)
pulumi.export("dev_workload_subnet_id", dev_workload_subnet.id)
pulumi.export("dev_tgw_subnet_a_id", dev_tgw_subnet_a.id)
pulumi.export("dev_tgw_subnet_b_id", dev_tgw_subnet_b.id)
pulumi.export("dev_instance_id", dev_instance.id)
pulumi.export("dev_instance_public_ip", dev_instance.public_ip)
pulumi.export("dev_instance_private_ip", dev_instance.private_ip)

# Transit Gateway
pulumi.export("transit_gateway_id", tgw.id)
pulumi.export("transit_gateway_arn", tgw.arn)
pulumi.export("transit_gateway_asn", tgw_amazon_side_asn)
pulumi.export("lab_tgw_attachment_id", lab_attachment.id)
pulumi.export("dev_tgw_attachment_id", dev_attachment.id)

# Testing Instructions
pulumi.export(
    "test_instructions",
    pulumi.Output.all(
        lab_instance.public_ip,
        dev_instance.private_ip,
        dev_instance.public_ip,
        lab_instance.private_ip,
    ).apply(
        lambda args: f"""
✅ Transit Gateway Configured!

CONNECTIVITY TEST:

1. SSH to Lab instance:
   ssh -i your-key.pem ec2-user@{args[0]}
   
2. From Lab instance, ping Dev instance private IP:
   ping {args[1]}
   
3. SSH to Dev instance:
   ssh -i your-key.pem ec2-user@{args[2]}
   
4. From Dev instance, ping Lab instance private IP:
   ping {args[3]}

Both pings should work through Transit Gateway! ✅

NOTE: Traffic flows through TGW (hub-and-spoke), NOT direct peering.
      This is transitive routing - Lab → TGW → Dev works!
      
COST WARNING: TGW costs $0.05/hour per attachment = $0.10/hour total
              Destroy immediately after testing!
"""
    ),
)

pulumi.log.info("✅ Transit Gateway deployment complete!")
