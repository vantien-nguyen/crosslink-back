# back-end

## Deployment

### Login AWS: 

```bash
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 943635619664.dkr.ecr.eu-west-3.amazonaws.com
```

### Staging: 
...

### Production: 

```bash
docker build -t crosslink-back:1.0.0 -f deployment/production/backend/Dockerfile . && \
docker tag crosslink-back:1.0.0 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-back:1.0.0 && \
docker push 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-back:1.0.0
```

```bash
docker build -t crosslink-worker:1.0.0 -f deployment/production/worker/Dockerfile . && \
docker tag crosslink-worker:1.0.0 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-worker:1.0.0 && \
docker push 943635619664.dkr.ecr.eu-west-3.amazonaws.com/crosslink-worker:1.0.0
```
