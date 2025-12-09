# 🌉 AWS Transit Gateway Hub-and-Spoke Architecture

Enterprise-grade multi-VPC networking using AWS Transit Gateway with hub-and-spoke topology. Demonstrates transitive routing, automatic route propagation, and multi-AZ high availability.

[![Infrastructure as Code](https://img.shields.io/badge/IaC-Pulumi-purple)](https://www.pulumi.com/)
[![AWS](https://img.shields.io/badge/AWS-Transit%20Gateway-orange)](https://aws.amazon.com/transit-gateway/)
[![LocalStack](https://img.shields.io/badge/LocalStack-Tested-green)](https://localstack.cloud/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

---

## 🎯 Project Overview

This project implements a production-ready AWS Transit Gateway architecture connecting multiple VPCs in a hub-and-spoke model. Unlike VPC Peering (which is non-transitive), Transit Gateway enables **transitive routing**, allowing all connected VPCs to communicate through a central hub.

### **Key Features**

- ✅ **Hub-and-Spoke Architecture** - Centralized routing through Transit Gateway
- ✅ **Transitive Routing** - VPC-A can reach VPC-C through the Transit Gateway
- ✅ **Automatic Route Propagation** - VPC CIDRs automatically added to TGW route table
- ✅ **Multi-AZ High Availability** - Dedicated TGW subnets in multiple availability zones
- ✅ **Scalable Design** - Linear scaling (O(N) vs O(N²) for VPC Peering)
- ✅ **LocalStack Testing** - Free local testing before AWS deployment
- ✅ **Production Best Practices** - Dedicated TGW subnets, proper tagging, security groups

---

## 🏗️ Architecture

### **High-Level Topology**

```
┌─────────────────────┐         ┌─────────────────────┐
│   Lab VPC           │         │   Dev VPC           │
│   10.200.0.0/16     │         │   10.201.0.0/16     │
│                     │         │                     │
│  ┌──────────────┐   │         │  ┌──────────────┐   │
│  │ Test Instance│   │         │  │ Test Instance│   │
│  │ 10.200.10.x  │   │         │  │ 10.201.10.x  │   │
│  └──────────────┘   │         │  └──────────────┘   │
│         ▲            │         │         ▲           │
│         │            │         │         │           │
│  ┌──────▼──────┐    │         │  ┌──────▼──────┐    │
│  │ TGW Subnet  │    │         │  │ TGW Subnet  │    │
│  │ (AZ-A, AZ-B)│    │         │  │ (AZ-A, AZ-B)│    │
│  └──────┬──────┘    │         │  └──────┬──────┘    │
└─────────┼───────────┘         └─────────┼───────────┘
          │                               │
          │         ┌───────────┐         │
          └────────▶│  Transit  │◀────────┘
                    │  Gateway  │
                    │   (Hub)   │
                    └───────────┘
```

### **Network Design**

**Lab VPC (10.200.0.0/16):**
- Workload Subnet: `10.200.10.0/24` (us-east-1a) - For test instances
- TGW Subnet A: `10.200.255.0/24` (us-east-1a) - Transit Gateway ENI
- TGW Subnet B: `10.200.254.0/24` (us-east-1b) - Transit Gateway ENI

**Dev VPC (10.201.0.0/16):**
- Workload Subnet: `10.201.10.0/24` (us-east-1a) - For test instances
- TGW Subnet A: `10.201.255.0/24` (us-east-1a) - Transit Gateway ENI
- TGW Subnet B: `10.201.254.0/24` (us-east-1b) - Transit Gateway ENI

**Transit Gateway:**
- BGP ASN: 64512 (configurable)
- Default route table: Enabled (automatic propagation)
- Multi-AZ: ENIs placed in us-east-1a and us-east-1b

---

## 🆚 Transit Gateway vs VPC Peering

| Feature | VPC Peering | Transit Gateway |
|---------|-------------|-----------------|
| **Transitive Routing** | ❌ No | ✅ Yes |
| **Scalability** | O(N²) connections | O(N) attachments |
| **10 VPCs** | 45 connections | 10 attachments |
| **Cost** | Free | $0.05/hour per attachment |
| **VPN Support** | No | Yes |
| **Best For** | 2-5 VPCs | 6+ VPCs, enterprise |

**Scalability Example:**
- 10 VPCs with Peering: **45 connections** required
- 10 VPCs with Transit Gateway: **10 attachments** required

---

## 💡 Key Concepts

### **1. Dedicated TGW Subnets**

**AWS Best Practice:** Create separate, dedicated subnets for Transit Gateway ENIs.

**Why?**
- Transit Gateway places ENIs in each availability zone
- Separate subnets provide clear organization
- Allows specific NACLs for TGW traffic
- Conserves IP addresses (use /28 or /29 in production)

**This project:** Uses /24 subnets for simplicity (production should use /28)

### **2. Automatic Route Propagation**

**When enabled (default):**
- VPC CIDRs automatically added to Transit Gateway route table
- No manual route management needed
- Simplifies configuration

**Example:**
```
Transit Gateway Route Table (automatic):
├── 10.200.0.0/16 → lab-vpc-attachment
└── 10.201.0.0/16 → dev-vpc-attachment
```

**Note:** VPC route tables still need manual routes pointing to Transit Gateway!

### **3. Transitive Routing**

**VPC Peering (Non-Transitive):**
```
VPC-A ↔ VPC-B, VPC-B ↔ VPC-C
VPC-A ✗ VPC-C (cannot communicate)
```

**Transit Gateway (Transitive):**
```
VPC-A → TGW → VPC-C ✅ (works!)
```

All VPCs connected to the Transit Gateway can communicate with each other.

### **4. Multi-AZ High Availability**

**Design:**
- TGW places ENI in each specified availability zone
- Traffic automatically fails over if one AZ fails
- No configuration needed - AWS handles it automatically

**This Project:**
- 2 TGW subnets per VPC (us-east-1a, us-east-1b)
- 4 total ENIs created by AWS (2 per VPC)

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.12+
- Pulumi CLI
- AWS credentials (for AWS deployment)
- Docker (for LocalStack testing)

### **Installation**

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/aws-transit-gateway-hub.git
cd aws-transit-gateway-hub

# Install dependencies
pip install -r requirements.txt
```

---

## 🐳 LocalStack Deployment (FREE)

Test infrastructure locally before deploying to AWS!

### **Step 1: Start LocalStack**

```bash
# Start LocalStack container
docker run -d \
  --name localstack \
  -p 4566:4566 \
  localstack/localstack

# Verify it's running
docker ps | grep localstack
```

### **Step 2: Configure LocalStack Stack**

```bash
# Initialize Pulumi stack for LocalStack
pulumi stack init tgw-local

# Set region
pulumi config set aws:region us-east-1

# LocalStack configuration (already in Pulumi.tgw-local.yaml)
pulumi config set aws:accessKey test
pulumi config set aws:secretKey test
pulumi config set aws:skipCredentialsValidation true
```

### **Step 3: Deploy**

```bash
# Set LocalStack endpoint
export AWS_ENDPOINT_URL=http://localhost:4566

# Deploy infrastructure
pulumi up

# Review changes and confirm
```

### **Step 4: Verify Resources**

```bash
# Check Transit Gateway
awslocal ec2 describe-transit-gateways

# Check VPC attachments
awslocal ec2 describe-transit-gateway-vpc-attachments

# Check route tables
awslocal ec2 describe-transit-gateway-route-tables

# Get Pulumi outputs
pulumi stack output
```

### **Step 5: Cleanup**

```bash
# Destroy infrastructure
pulumi destroy

# Stop LocalStack
docker stop localstack
docker rm localstack
```

**Cost:** $0.00 ✅

---

## ☁️ AWS Deployment

### **Cost Warning** ⚠️

Transit Gateway costs **$0.05/hour per attachment**. For this project:
- 2 VPC attachments = $0.10/hour
- **Monthly cost: ~$73** if left running
- **Test deployment (30 min): ~$0.05**

**Always destroy resources after testing!**

### **Step 1: Configure AWS Stack**

```bash
# Initialize AWS stack
pulumi stack init tgw-aws

# Set region
pulumi config set aws:region us-east-1

# Optional: Set SSH key for instance access
pulumi config set key_name your-ssh-key-name

# Optional: Customize VPC CIDRs
pulumi config set lab_vpc_cidr 10.200.0.0/16
pulumi config set dev_vpc_cidr 10.201.0.0/16
```

### **Step 2: Deploy to AWS**

```bash
# Deploy (takes ~5-7 minutes)
pulumi up

# Review changes
# Confirm: yes
```

### **Step 3: Test Connectivity**

```bash
# Get instance IPs
export LAB_PUBLIC=$(pulumi stack output lab_instance_public_ip)
export DEV_PRIVATE=$(pulumi stack output dev_instance_private_ip)

# SSH to Lab instance
ssh -i ~/.ssh/your-key.pem ec2-user@$LAB_PUBLIC

# Inside Lab instance, ping Dev instance
ping $DEV_PRIVATE
# Expected: Success! Traffic flows through Transit Gateway
```

### **Step 4: Verify Transit Gateway**

**AWS Console:**
1. Navigate to **VPC** → **Transit Gateways**
2. Verify status: **Available**
3. Check **Attachments** tab - both VPCs should be attached
4. View **Route Tables** → Routes should show both VPC CIDRs

**CLI:**
```bash
# Check Transit Gateway status
aws ec2 describe-transit-gateways \
  --query 'TransitGateways[0].State'

# Check attachments
aws ec2 describe-transit-gateway-vpc-attachments \
  --query 'TransitGatewayVpcAttachments[*].[VpcId,State]'

# Check TGW route table
aws ec2 describe-transit-gateway-route-tables
```

### **Step 5: Destroy Resources** 🚨

**CRITICAL:** Destroy immediately after testing to avoid costs!

```bash
# Destroy all resources
pulumi destroy

# Confirm: yes

# Verify destruction
aws ec2 describe-transit-gateways
# Should return empty or "deleted" state
```

---

## 📊 Resources Created

**Total:** ~24 AWS resources

### **Per VPC (x2):**
- 1 VPC
- 3 Subnets (1 workload + 2 TGW)
- 1 Internet Gateway
- 1 Route Table
- 1 Security Group
- 1 EC2 Instance

### **Transit Gateway:**
- 1 Transit Gateway
- 2 VPC Attachments
- 4 ENIs (2 per VPC, placed by AWS)
- 2 VPC routes (pointing to TGW)

---

## 🔧 Configuration Options

### **Pulumi Configuration**

```yaml
# VPC CIDRs
lab_vpc_cidr: "10.200.0.0/16"          # Lab VPC CIDR
dev_vpc_cidr: "10.201.0.0/16"          # Dev VPC CIDR

# Subnet CIDRs
lab_subnet_cidr: "10.200.10.0/24"      # Lab workload subnet
dev_subnet_cidr: "10.201.10.0/24"      # Dev workload subnet

# Transit Gateway subnets
lab_tgw_subnet_a_cidr: "10.200.255.0/24"  # Lab TGW AZ-A
lab_tgw_subnet_b_cidr: "10.200.254.0/24"  # Lab TGW AZ-B
dev_tgw_subnet_a_cidr: "10.201.255.0/24"  # Dev TGW AZ-A
dev_tgw_subnet_b_cidr: "10.201.254.0/24"  # Dev TGW AZ-B

# Instance configuration
instance_type: "t3.micro"              # EC2 instance type
key_name: "your-ssh-key"               # SSH key name (optional)

# Transit Gateway configuration
tgw_asn: 64512                         # BGP ASN
tgw_use_default_rt: true               # Use default route table
```

### **Setting Configuration**

```bash
# Set any configuration value
pulumi config set <key> <value>

# Example: Change instance type
pulumi config set instance_type t3.small

# Example: Set SSH key
pulumi config set key_name my-key-pair
```

---

## 🧪 Testing

### **Connectivity Testing**

**Test 1: Ping between VPCs**
```bash
# From Lab instance to Dev instance
ping 10.201.10.x

# From Dev instance to Lab instance
ping 10.200.10.x
```

**Test 2: Verify TGW Status**
```bash
# Check Transit Gateway state
aws ec2 describe-transit-gateways \
  --filters "Name=state,Values=available"
```

**Test 3: Verify Route Propagation**
```bash
# Check TGW route table
aws ec2 describe-transit-gateway-route-tables

# Routes should show both VPC CIDRs automatically propagated
```

### **LocalStack vs AWS**

| Test | LocalStack | AWS |
|------|------------|-----|
| **Infrastructure validation** | ✅ Yes | ✅ Yes |
| **Resource creation** | ✅ Yes | ✅ Yes |
| **Connectivity testing** | ❌ No | ✅ Yes |
| **Cost** | Free | ~$0.05 for 30 min |

**Recommendation:** Validate infrastructure on LocalStack first, then briefly test connectivity on AWS.

---

## 📁 Project Structure

```
aws_transit_gateway_hub/
├── __main__.py              # Main Pulumi program
├── tgw.py                   # Transit Gateway module
├── vpc.py                   # VPC creation module
├── networking.py            # Networking utilities
├── Pulumi.yaml              # Project configuration
├── Pulumi.tgw-local.yaml    # LocalStack stack configuration
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── .gitignore               # Git ignore rules
│
└── docs/                    # Documentation
    ├── ARCHITECTURE.md      # Architecture deep dive
    ├── DEPLOYMENT_GUIDE.md  # Step-by-step deployment
    └── QUICK_REF.md         # Quick reference
```

---

## 🎓 Learning Outcomes

### **Technical Skills**

- ✅ Hub-and-spoke network architecture
- ✅ Transit Gateway operations and configuration
- ✅ Transitive routing concepts
- ✅ Multi-AZ high availability design
- ✅ Automatic route propagation
- ✅ AWS networking best practices
- ✅ Infrastructure as Code with Pulumi

### **AWS Services**

- ✅ AWS Transit Gateway
- ✅ VPC networking
- ✅ Route tables and routing
- ✅ Security groups
- ✅ Elastic Network Interfaces (ENIs)
- ✅ EC2 instances

---

## 💼 Portfolio Value

### **Resume Bullets**

- "Designed and deployed AWS Transit Gateway hub-and-spoke architecture connecting multiple VPCs with automatic route propagation"
- "Reduced multi-VPC connectivity complexity from O(N²) to O(N) using centralized Transit Gateway routing"
- "Implemented multi-AZ high availability with dedicated Transit Gateway subnets across availability zones"

### **Interview Talking Points**

**On Scalability:**
> "Transit Gateway solves the scalability problem of VPC Peering. For 10 VPCs, VPC Peering requires 45 connections (N×(N-1)/2), but Transit Gateway only needs 10 attachments. This linear scaling is critical for enterprise networks."

**On Transitive Routing:**
> "Unlike VPC Peering which is non-transitive, Transit Gateway enables transitive routing. If VPC-A connects to the TGW and VPC-B connects to the TGW, then VPC-A can reach VPC-B through the Transit Gateway automatically."

**On High Availability:**
> "We deploy dedicated TGW subnets in multiple availability zones. AWS automatically places ENIs in each AZ, providing automatic failover if one AZ becomes unavailable."

---

## 🔍 Troubleshooting

### **Issue: Ping fails between VPCs**

**Check:**
1. Transit Gateway status is "available"
2. VPC attachments status is "available"
3. Routes exist in VPC route tables pointing to TGW
4. Security groups allow ICMP from peer VPC CIDR
5. ENIs exist in TGW subnets

**Solution:**
```bash
# Verify TGW status
aws ec2 describe-transit-gateways

# Verify attachments
aws ec2 describe-transit-gateway-vpc-attachments

# Check VPC route tables
aws ec2 describe-route-tables
```

### **Issue: LocalStack resources not appearing**

**Check:**
```bash
# Verify LocalStack is running
docker ps | grep localstack

# Check endpoint configuration
cat Pulumi.tgw-local.yaml

# Verify AWS_ENDPOINT_URL is set
echo $AWS_ENDPOINT_URL
```

### **Issue: High AWS costs**

**Solution:**
```bash
# Destroy resources immediately
pulumi destroy --yes

# Verify destruction
aws ec2 describe-transit-gateways
```

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture deep dive
- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Step-by-step deployment instructions
- **[QUICK_REF.md](docs/QUICK_REF.md)** - Quick reference guide

---

## 🤝 Contributing

This is a portfolio/learning project. Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests
- Use as a learning resource

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Tutorial based on [PacketSwitch.co.uk AWS Transit Gateway Introduction](https://www.packetswitch.co.uk/aws-transit-gateway-introduction/)
- Built with [Pulumi](https://www.pulumi.com/)
- Tested with [LocalStack](https://localstack.cloud/)

---

## 📞 Questions?

For questions or discussions about this project:
- Check the [documentation](docs/)
- Review AWS Transit Gateway [official docs](https://docs.aws.amazon.com/vpc/latest/tgw/)
- See Pulumi [AWS examples](https://github.com/pulumi/examples/tree/master/aws-py-vpc)

---

**Built with ❤️ for learning AWS networking**

**Remember: Always destroy AWS resources after testing to avoid unnecessary costs!**