#!/bin/bash
set -e

# NetLedger Self-Hosted Installer
# Usage: curl -fsSL https://netl.2max.tech/install.sh | sudo bash

INSTALL_DIR="/opt/netledger"
REPO_URL="https://github.com/2maxtech/NetLedger.git"
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${ORANGE}╔══════════════════════════════════════╗${NC}"
echo -e "${ORANGE}║       ${BOLD}NetLedger Installer${NC}${ORANGE}            ║${NC}"
echo -e "${ORANGE}║    ISP Billing & MikroTik Manager    ║${NC}"
echo -e "${ORANGE}║           by 2max Tech               ║${NC}"
echo -e "${ORANGE}╚══════════════════════════════════════╝${NC}"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root: sudo bash install.sh${NC}"
  exit 1
fi

# Check OS
if [ ! -f /etc/debian_version ] && [ ! -f /etc/lsb-release ]; then
  echo -e "${RED}This installer requires Debian or Ubuntu.${NC}"
  exit 1
fi

# Step 1: Install dependencies
echo -e "${GREEN}[1/6]${NC} Installing dependencies..."
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg git > /dev/null 2>&1
echo -e "  ${GREEN}Done${NC}"

# Step 2: Install Docker
echo -e "${GREEN}[2/6]${NC} Installing Docker..."
if ! command -v docker &> /dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin > /dev/null 2>&1
  systemctl enable docker > /dev/null 2>&1
  systemctl start docker
  echo -e "  ${GREEN}Docker installed${NC}"
else
  echo -e "  ${GREEN}Docker already installed${NC}"
fi

# Step 3: Clone or update repo
echo -e "${GREEN}[3/6]${NC} Downloading NetLedger..."
if [ -d "$INSTALL_DIR/.git" ]; then
  cd $INSTALL_DIR
  git pull --quiet
  echo -e "  ${GREEN}Updated to latest${NC}"
else
  rm -rf $INSTALL_DIR
  git clone --quiet --depth 1 $REPO_URL $INSTALL_DIR
  cd $INSTALL_DIR
  echo -e "  ${GREEN}Downloaded${NC}"
fi

# Step 4: Generate config
echo -e "${GREEN}[4/6]${NC} Configuring..."
DB_PASS=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)

if [ ! -f "$INSTALL_DIR/.env" ]; then
  cat > $INSTALL_DIR/.env << ENVFILE
POSTGRES_USER=netledger
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_DB=netledger
DATABASE_URL=postgresql+asyncpg://netledger:$DB_PASS@db:5432/netledger
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$SECRET_KEY
MIKROTIK_URL=http://192.168.88.1
MIKROTIK_USER=admin
MIKROTIK_PASSWORD=
ENVFILE
  echo -e "  ${GREEN}Config created${NC}"
else
  echo -e "  ${GREEN}Config exists, keeping current${NC}"
fi

# Step 5: Build and start
echo -e "${GREEN}[5/6]${NC} Building and starting NetLedger (this may take a few minutes)..."
cd $INSTALL_DIR
docker compose build --quiet 2>&1 | tail -1
docker compose up -d 2>&1 | tail -1
echo -e "  ${GREEN}Services started${NC}"

# Step 6: Database setup
echo -e "${GREEN}[6/6]${NC} Setting up database..."
sleep 5

# Wait for DB to be ready
for i in $(seq 1 30); do
  docker compose exec -T db pg_isready -U netledger > /dev/null 2>&1 && break
  sleep 1
done

docker compose exec -T backend alembic upgrade head 2>/dev/null || echo "  Migration note: may need manual intervention"

# Create admin user
ADMIN_PASS="admin123"
docker compose exec -T backend python3 -c "
import asyncio
from app.core.database import async_session
from app.models.user import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select

async def seed():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            return
        admin = User(
            username='admin',
            email='admin@localhost',
            password_hash=hash_password('$ADMIN_PASS'),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

asyncio.run(seed())
" 2>/dev/null

LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ${BOLD}NetLedger installed successfully!${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Open in browser:${NC} ${ORANGE}http://$LOCAL_IP${NC}"
echo ""
echo -e "  ${BOLD}Login:${NC}"
echo -e "    Username: ${ORANGE}admin${NC}"
echo -e "    Password: ${ORANGE}$ADMIN_PASS${NC}"
echo ""
echo -e "  ${BOLD}Next steps:${NC}"
echo -e "    1. Change your admin password"
echo -e "    2. Go to Setup Guide in the sidebar"
echo -e "    3. Add your MikroTik router (use local IP!)"
echo -e "    4. Create plans and add customers"
echo ""
echo -e "  ${BOLD}Manage:${NC}"
echo -e "    cd $INSTALL_DIR"
echo -e "    docker compose logs -f      ${GREEN}# view logs${NC}"
echo -e "    docker compose down          ${GREEN}# stop${NC}"
echo -e "    docker compose up -d         ${GREEN}# start${NC}"
echo ""
echo -e "  ${BOLD}Update:${NC}"
echo -e "    cd $INSTALL_DIR && git pull && docker compose build && docker compose up -d"
echo ""
echo -e "  ${ORANGE}⚠  Change your admin password after first login!${NC}"
echo ""
