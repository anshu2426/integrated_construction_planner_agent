# CI/CD Deployment Checklist

Use this checklist for quick reference during deployment.

## Pre-Deployment Checklist

- [ ] AWS Account with EC2 access
- [ ] Docker Hub account created
- [ ] GitHub repository ready
- [ ] SSH key pair generated for EC2
- [ ] Groq API key obtained

---

## Phase 1: EC2 Setup

- [ ] Launch EC2 instance (Ubuntu 22.04, t3.medium)
- [ ] Configure security group (Ports 22, 8501)
- [ ] SSH into EC2 instance
- [ ] Install Docker and Docker Compose
- [ ] Create application directory `~/construction-planner`
- [ ] Create `.env` file with `GROQ_API_KEY`
- [ ] Create `docker-compose.yml` file

---

## Phase 2: Docker Hub Setup

- [ ] Log in to Docker Hub
- [ ] Create access token (Read, Write, Delete permissions)
- [ ] Save access token securely
- [ ] Note Docker Hub username

---

## Phase 3: GitHub Actions Setup

- [ ] Go to GitHub repo → Settings → Secrets
- [ ] Add `DOCKER_USERNAME` secret
- [ ] Add `DOCKER_PASSWORD` secret (access token)
- [ ] Add `EC2_INSTANCE_IP` secret
- [ ] Add `EC2_USERNAME` secret (ubuntu)
- [ ] Add `EC2_SSH_KEY` secret (full .pem content)

---

## Phase 4: Deploy

- [ ] Commit changes: `git add . && git commit -m "Configure CI/CD"`
- [ ] Push to main: `git push origin main`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify workflow completes successfully
- [ ] SSH into EC2 and check container status
- [ ] Access application at `http://<EC2-IP>:8501`

---

## Post-Deployment Verification

- [ ] Container is running: `docker ps`
- [ ] Application accessible in browser
- [ ] No errors in logs: `docker-compose logs -f`
- [ ] Health check passing: `docker inspect construction-planner`

---

## Troubleshooting Quick Reference

**Workflow fails:**
- Check GitHub Secrets are correct
- Verify Docker Hub token is valid
- Ensure EC2 is running and accessible

**Container not starting:**
- Check `.env` file has correct API key
- Verify port 8501 is not in use
- Review logs: `docker-compose logs app`

**Application not accessible:**
- Verify security group allows port 8501
- Check container is running
- Verify EC2 public IP is correct

---

## Common Commands

```bash
# SSH into EC2
ssh -i /path/to/key.pem ubuntu@<EC2-IP>

# Check container status
cd ~/construction-planner && docker-compose ps

# View logs
cd ~/construction-planner && docker-compose logs -f

# Restart application
cd ~/construction-planner && docker-compose restart

# Pull latest and restart
cd ~/construction-planner && docker-compose pull && docker-compose up -d
```

---

## Next Steps (Optional)

- [ ] Set up custom domain name
- [ ] Configure Nginx reverse proxy
- [ ] Add SSL certificate with Certbot
- [ ] Set up monitoring and alerts
- [ ] Configure backup strategy
- [ ] Set up auto-scaling (if needed)

---

**For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)**
