# CI/CD Pipeline for EC2 Deployment

## Overview

This document provides a complete process for deploying the Construction Planning Agent to AWS EC2 using GitHub Actions CI/CD pipeline with Docker.

## Architecture

```
GitHub Repository → GitHub Actions → Docker Hub → EC2 Instance
                                                     ↓
                                              Docker Compose
                                                     ↓
                                              Streamlit App (Port 8501)
```

## Prerequisites

- AWS Account with EC2 access
- Docker Hub account
- GitHub repository
- SSH key pair for EC2 access
- Groq API key

---

## Phase 1: AWS EC2 Setup

### 1.1 Launch EC2 Instance

1. **Go to AWS Console** → EC2 → Launch Instance
2. **Configure Instance:**
   - Name: `construction-planner`
   - OS: Ubuntu 22.04 LTS
   - Instance Type: `t3.medium` (recommended) or `t3.large`
   - Key Pair: Create or use existing SSH key pair
   - Storage: 20GB GP3

3. **Network Settings:**
   - Create new security group or use existing
   - Allow SSH (Port 22) from your IP
   - Allow HTTP (Port 80) from 0.0.0.0/0 (optional, for load balancer)
   - Allow Custom TCP (Port 8501) from 0.0.0.0/0

4. **Launch Instance** and note the:
   - Public IP address
   - Private key file location (.pem)

### 1.2 Configure Security Group

Navigate to EC2 → Security Groups → Inbound Rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP/32 | SSH access |
| Custom TCP | TCP | 8501 | 0.0.0.0/0 | Streamlit app |
| HTTP | TCP | 80 | 0.0.0.0/0 | Optional (for Nginx) |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Optional (for SSL) |

### 1.3 Connect to EC2 and Install Docker

```bash
# SSH into EC2
ssh -i /path/to/your-key-pair.pem ubuntu@<EC2-PUBLIC-IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and log back in for group changes to take effect
exit
```

### 1.4 Setup Application Directory

```bash
# SSH back into EC2
ssh -i /path/to/your-key-pair.pem ubuntu@<EC2-PUBLIC-IP>

# Create application directory
mkdir -p ~/construction-planner
cd ~/construction-planner

# Create .env file
nano .env
```

Add the following to `.env`:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
PYTHONUNBUFFERED=1
```

### 1.5 Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
services:
  app:
    image: ${DOCKER_IMAGE:-your-dockerhub-username/construction-planner}:latest
    container_name: construction-planner
    ports:
      - "8501:8501"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8501')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
```

**Replace** `your-dockerhub-username` with your actual Docker Hub username.

---

## Phase 2: Docker Hub Setup

### 2.1 Create Docker Hub Account

1. Go to [Docker Hub](https://hub.docker.com/)
2. Sign up or log in
3. Note your username

### 2.2 Create Access Token

1. Go to Docker Hub → Account Settings → Security → New Access Token
2. Token description: `GitHub Actions CI/CD`
3. Access permissions: Read, Write, Delete
4. Copy the generated token (save it securely)

### 2.3 Test Docker Hub Access (Optional)

```bash
# On your local machine
docker login
# Enter username and access token

# Test build and push
docker build -t your-username/construction-planner:test .
docker push your-username/construction-planner:test
```

---

## Phase 3: GitHub Actions CI/CD Setup

### 3.1 Workflow File Structure

Your workflow file is at `.github/workflows/deploy.yml` and includes:
- Build and push Docker image to Docker Hub
- Deploy to EC2 via SSH
- Automatic cleanup of old images

### 3.2 Configure GitHub Secrets

Navigate to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKER_USERNAME` | Your Docker Hub username | Docker Hub login |
| `DOCKER_PASSWORD` | Docker Hub access token | Generated in Phase 2.2 |
| `EC2_INSTANCE_IP` | EC2 public IP address | e.g., 54.123.45.67 |
| `EC2_USERNAME` | `ubuntu` | EC2 SSH user |
| `EC2_SSH_KEY` | Private SSH key content | Full content of .pem file |

**Important:** For `EC2_SSH_KEY`, copy the entire content of your private key file including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`.

### 3.3 Workflow Triggers

The workflow triggers on:
- Push to `main` branch
- Manual trigger via `workflow_dispatch` (GitHub Actions tab → Run workflow)

---

## Phase 4: Deployment Process

### 4.1 Initial Deployment

```bash
# On your local machine
git add .
git commit -m "Configure CI/CD deployment"
git push origin main
```

The GitHub Actions workflow will:
1. Build Docker image with cache optimization
2. Push image to Docker Hub with tags: `latest` and commit SHA
3. SSH into EC2
4. Stop existing containers
5. Pull latest image
6. Start containers with docker-compose
7. Clean up old images

### 4.2 Monitor Deployment

1. Go to GitHub repository → Actions tab
2. Click on the running workflow
3. View real-time logs for each step

### 4.3 Verify Deployment

```bash
# SSH into EC2
ssh -i /path/to/your-key-pair.pem ubuntu@<EC2-PUBLIC-IP>

# Check container status
cd ~/construction-planner
docker-compose ps

# View logs
docker-compose logs -f

# Check container health
docker inspect construction-planner | grep -A 10 Health
```

### 4.4 Access Application

Open browser: `http://<EC2-PUBLIC-IP>:8501`

---

## Phase 5: Environment Management

### 5.1 Update Environment Variables

```bash
# SSH into EC2
ssh -i /path/to/your-key-pair.pem ubuntu@<EC2-PUBLIC-IP>
cd ~/construction-planner

# Edit .env file
nano .env

# Restart container to apply changes
docker-compose down
docker-compose up -d
```

### 5.2 Update Groq API Key

```bash
# On EC2
cd ~/construction-planner
sed -i 's/GROQ_API_KEY=.*/GROQ_API_KEY=new_key_here/' .env
docker-compose restart
```

---

## Phase 6: Monitoring and Maintenance

### 6.1 View Application Logs

```bash
# SSH into EC2
cd ~/construction-planner

# Real-time logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Logs since specific time
docker-compose logs --since 2024-01-01T00:00:00 app
```

### 6.2 Container Health Check

```bash
# Check container status
docker ps

# Detailed health status
docker inspect construction-planner | jq '.[0].State.Health'
```

### 6.3 System Resources

```bash
# CPU and Memory usage
docker stats

# Disk usage
df -h

# Docker disk usage
docker system df
```

### 6.4 Cleanup Old Images

```bash
# Remove unused images
docker image prune -a

# Remove all stopped containers
docker container prune

# Complete cleanup (use with caution)
docker system prune -a --volumes
```

---

## Phase 7: Troubleshooting

### 7.1 Deployment Failures

**GitHub Actions fails at Docker login:**
- Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
- Check Docker Hub token permissions
- Ensure token hasn't expired

**GitHub Actions fails at SSH:**
- Verify `EC2_INSTANCE_IP` is correct
- Check `EC2_SSH_KEY` format (include full key content)
- Ensure EC2 security group allows SSH from GitHub Actions IP ranges
- Verify EC2 instance is running

**Docker pull fails on EC2:**
- Check internet connectivity on EC2
- Verify Docker Hub image exists
- Check image name matches Docker Hub username

### 7.2 Application Issues

**Container not starting:**
```bash
# Check logs
docker-compose logs app

# Common issues:
# - Missing GROQ_API_KEY in .env
# - Port 8501 already in use
# - Insufficient resources
```

**Application not accessible:**
- Verify EC2 security group allows port 8501
- Check if container is running: `docker ps`
- Verify port mapping: `docker port construction-planner`
- Check AWS EC2 network ACLs

**High memory usage:**
- Upgrade to larger instance type (t3.large or t3.xlarge)
- Add memory limits to docker-compose.yml
- Monitor with `docker stats`

### 7.3 Rollback Deployment

```bash
# SSH into EC2
cd ~/construction-planner

# Pull specific version
docker pull your-username/construction-planner:<commit-sha>

# Update docker-compose.yml to use specific tag
sed -i 's/:latest/:<commit-sha>/' docker-compose.yml

# Restart
docker-compose down
docker-compose up -d
```

---

## Phase 8: Advanced Configuration

### 8.1 Add Nginx Reverse Proxy (Optional)

```bash
# Install Nginx on EC2
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/construction-planner
```

Add to Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/construction-planner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8.2 Add SSL Certificate (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### 8.3 Add Domain Name

1. Purchase domain from registrar
2. Create A record pointing to EC2 public IP
3. Update Nginx config with domain name
4. Obtain SSL certificate

### 8.4 Configure Auto-scaling (Advanced)

- Use AWS Application Load Balancer
- Configure Auto Scaling Group
- Update security groups for ALB
- Modify GitHub Actions to deploy to multiple instances

---

## Phase 9: Security Best Practices

### 9.1 SSH Key Management

- Use different SSH keys for different environments
- Rotate SSH keys regularly
- Never commit private keys to repository
- Use AWS Systems Manager Session Manager for SSH-less access

### 9.2 Environment Variables

- Never commit `.env` files
- Use GitHub Secrets for sensitive data
- Rotate API keys regularly
- Use AWS Secrets Manager for production

### 9.3 Container Security

- Use specific image tags instead of `latest` in production
- Scan images for vulnerabilities: `docker scan`
- Keep base images updated
- Minimize container privileges

### 9.4 Network Security

- Use security groups to restrict access
- Enable VPC flow logs for monitoring
- Use AWS WAF for web application firewall
- Implement IP whitelisting where possible

---

## Phase 10: Cost Optimization

### 10.1 EC2 Cost Management

- Use Reserved Instances for long-running workloads
- Consider Spot Instances for non-critical workloads
- Stop instances when not in use
- Use AWS Cost Explorer to monitor spending

### 10.2 Docker Hub Limits

- Free tier: 1 private repository, unlimited public
- Consider AWS ECR for better AWS integration
- Use multi-stage builds to reduce image size

---

## Quick Reference Commands

```bash
# SSH into EC2
ssh -i /path/to/key.pem ubuntu@<EC2-IP>

# View container logs
cd ~/construction-planner && docker-compose logs -f

# Restart application
cd ~/construction-planner && docker-compose restart

# Pull latest and restart
cd ~/construction-planner && docker-compose pull && docker-compose up -d

# Check container status
docker ps

# Remove old images
docker image prune -a

# Update .env file
cd ~/construction-planner && nano .env && docker-compose restart
```

---

## Support and Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)

---

**Last Updated:** April 2026
