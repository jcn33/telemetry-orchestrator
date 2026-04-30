#!/bin/bash
# infra/bootstrap_ec2.sh
# One-time setup for the telemetry-orchestrator EC2 dev server.
# Runs automatically via user-data on new instances, or manually via scp for existing ones.
# Logs to: /var/log/bootstrap_ec2.log

set -euo pipefail
exec > >(tee -a /var/log/bootstrap_ec2.log) 2>&1

echo "======================================================"
echo " telemetry-orchestrator bootstrap starting"
echo " $(date)"
echo "======================================================"

# ── System ────────────────────────────────────────────────────────────────────
echo "[1/7] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -yq
apt-get install -yq \
  curl wget unzip git build-essential \
  ca-certificates gnupg lsb-release \
  software-properties-common

# ── Docker ────────────────────────────────────────────────────────────────────
echo "[2/7] Installing Docker CE..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -q
apt-get install -yq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
echo "  -> Docker $(docker --version)"
echo "  -> Docker Compose $(docker compose version)"

# ── Python ────────────────────────────────────────────────────────────────────
echo "[3/7] Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -q
apt-get install -yq python3.11 python3.11-venv python3.11-dev python3-pip
# update-alternatives runs AFTER Node.js — NodeSource setup script requires
# python3 to point to the system default (3.10) or apt_pkg breaks.
echo "  -> Python 3.11 installed"

# ── Node.js 20 LTS ───────────────────────────────────────────────────────────
echo "[4/7] Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -yq nodejs
# Now safe to switch python3 default — NodeSource is done with apt
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
echo "  -> $(node --version)"
echo "  -> npm $(npm --version)"
echo "  -> $(python3 --version)"

# ── Claude Code CLI ───────────────────────────────────────────────────────────
echo "[5/7] Installing Claude Code CLI..."
npm install -g @anthropic-ai/claude-code
echo "  -> $(claude --version)"

# ── AWS CLI v2 ────────────────────────────────────────────────────────────────
echo "[6/7] Installing AWS CLI v2..."
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install
rm -rf /tmp/awscliv2.zip /tmp/aws
echo "  -> $(aws --version)"

# ── GitHub SSH Key ────────────────────────────────────────────────────────────
echo "[7/7] Generating GitHub SSH key for ubuntu user..."
sudo -u ubuntu ssh-keygen -t ed25519 -C "telemetry-dev-ec2" -f /home/ubuntu/.ssh/id_ed25519 -N ""
sudo -u ubuntu cp /home/ubuntu/.ssh/id_ed25519.pub /home/ubuntu/github_deploy_key.pub
echo "  -> Public key saved to ~/github_deploy_key.pub"

# ── Git defaults ──────────────────────────────────────────────────────────────
sudo -u ubuntu git config --global init.defaultBranch main
sudo -u ubuntu git config --global core.editor "code --wait"

# ── Done ──────────────────────────────────────────────────────────────────────
touch /home/ubuntu/bootstrap_complete
echo ""
echo "======================================================"
echo " Bootstrap complete — $(date)"
echo "======================================================"
echo ""
echo " NEXT STEPS:"
echo " 1. cat ~/github_deploy_key.pub"
echo "    -> Add to GitHub: Settings > SSH keys"
echo " 2. git clone git@github.com:jcn33/telemetry-orchestrator.git"
echo " 3. cd telemetry-orchestrator && cp .env.example .env"
echo "    -> Fill in secrets in .env"
echo " 4. claude"
echo "    -> Authenticate Claude Code (browser OAuth)"
echo "======================================================"
