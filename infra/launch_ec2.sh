#!/bin/bash
# infra/launch_ec2.sh
# Provisions the telemetry-orchestrator dev server on AWS EC2.
# Usage: KEY_NAME=my-key-pair ./infra/launch_ec2.sh

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
INSTANCE_NAME="telemetry-dev-server"
INSTANCE_TYPE="t3.xlarge"
REGION="us-west-2"
SECURITY_GROUP="telemetry-sg"
VOLUME_SIZE=30

# Require key pair name
if [[ -z "${KEY_NAME:-}" ]]; then
  echo "ERROR: KEY_NAME environment variable is required."
  echo "Usage: KEY_NAME=my-key-pair ./infra/launch_ec2.sh"
  exit 1
fi

# ── Resolve current IP for SSH allowlist ─────────────────────────────────────
echo "Resolving your current public IP..."
MY_IP=$(curl -sf https://checkip.amazonaws.com)/32
echo "  -> Restricting SSH to: $MY_IP"

# ── Resolve latest Ubuntu 22.04 LTS AMI (us-west-2) ─────────────────────────
echo "Resolving latest Ubuntu 22.04 LTS AMI in $REGION..."
AMI_ID=$(aws ssm get-parameter \
  --region "$REGION" \
  --name /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
  --query 'Parameter.Value' \
  --output text)
echo "  -> Using AMI: $AMI_ID"

# ── Security Group ────────────────────────────────────────────────────────────
echo "Creating security group '$SECURITY_GROUP'..."
SG_ID=$(aws ec2 create-security-group \
  --region "$REGION" \
  --group-name "$SECURITY_GROUP" \
  --description "telemetry-orchestrator dev server — SSH only" \
  --query 'GroupId' \
  --output text 2>/dev/null) || {
    echo "  -> Security group already exists, fetching ID..."
    SG_ID=$(aws ec2 describe-security-groups \
      --region "$REGION" \
      --group-names "$SECURITY_GROUP" \
      --query 'SecurityGroups[0].GroupId' \
      --output text)
  }
echo "  -> Security Group ID: $SG_ID"

# SSH restricted to current IP only — all other access via VS Code port forwarding
aws ec2 authorize-security-group-ingress \
  --region "$REGION" \
  --group-id "$SG_ID" \
  --protocol tcp --port 22 --cidr "$MY_IP" 2>/dev/null || true

# ── Launch Instance ───────────────────────────────────────────────────────────
echo "Launching EC2 instance ($INSTANCE_TYPE)..."
INSTANCE_ID=$(aws ec2 run-instances \
  --region "$REGION" \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --count 1 \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
  --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$VOLUME_SIZE,\"VolumeType\":\"gp3\"}}]" \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "  -> Instance ID: $INSTANCE_ID"

# ── Wait for running state ────────────────────────────────────────────────────
echo "Waiting for instance to reach running state..."
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"

# ── Output connection details ─────────────────────────────────────────────────
PUBLIC_IP=$(aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " telemetry-dev-server is live"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Instance ID : $INSTANCE_ID"
echo " Public IP   : $PUBLIC_IP"
echo " Region      : $REGION"
echo ""
echo " SSH:  ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo " VS Code Remote SSH config (~/.ssh/config):"
echo "   Host telemetry-dev"
echo "     HostName $PUBLIC_IP"
echo "     User ubuntu"
echo "     IdentityFile ~/.ssh/$KEY_NAME.pem"
echo "     LocalForward 3000 localhost:3000"
echo "     LocalForward 8000 localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
