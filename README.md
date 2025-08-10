# CLO835 Final Project – Flask + MySQL on Amazon EKS

## 📌 Overview
This project demonstrates deploying a Python Flask web application with a MySQL database on **Amazon EKS**.  
It showcases:
- Persistent storage using **Amazon EBS**
- Private image storage on **Amazon ECR**
- Background image loading from a **private Amazon S3 bucket**
- Secrets & ConfigMaps for sensitive configuration
- GitHub Actions CI/CD pipeline for automated image build & push


## ⚙ Features Implemented
1. **Flask application** runs on port `81` and fetches:
   - Background image URL from **ConfigMap**
   - MySQL credentials from **Kubernetes Secrets**
2. **MySQL database** deployed with PersistentVolume (Amazon EBS) to retain data even if the pod restarts.
3. **S3 background image** download with AWS credentials stored as Kubernetes Secret.
4. **Private ECR** image hosting and pulling via imagePullSecrets.
5. **CI/CD with GitHub Actions**:
   - On push, builds & pushes image to Amazon ECR.
   - Automatically deploys latest image to EKS.

---


## ☁ Deployment on Amazon EKS
1️⃣ Create Namespace
```bash 
kubectl create ns fp
```
2️⃣ Apply Manifests
```bash
kubectl apply -f k8s/
```
3️⃣ Access Web Application
```bash
kubectl -n fp get svc webapp
```
Visit: http://LoadBalancerDNS:81


📂 Persistent Storage Verification

Delete MySQL pod:

```bash
kubectl -n fp delete pod <mysql-pod>
```
Data remains in Amazon EBS volume and is re-attached to new pod.

🔄 Change Background Image

Upload a new image to S3.

Update BG_S3_KEY in k8s/app-config.yaml:

```yaml
BG_S3_KEY: images/new-bg.jpg
```
Apply config and restart webapp:
```
kubectl -n fp apply -f k8s/app-config.yaml
kubectl -n fp rollout restart deploy/webapp
```
🛑 Secrets Note
- k8s/aws-secret.yaml and k8s/db-secret.yaml are not included in GitHub for security reasons.
Create them locally before deploying:
```bash
kubectl create secret generic aws-secret \
  --from-literal=AWS_ACCESS_KEY_ID=... \
  --from-literal=AWS_SECRET_ACCESS_KEY=... \
  --from-literal=AWS_SESSION_TOKEN=... \
  --from-literal=AWS_REGION=us-east-1 \
  -n fp

kubectl create secret generic db-secret \
  --from-literal=DBUSER=root \
  --from-literal=DBPWD=yourpassword \
  --from-literal=MYSQL_ROOT_PASSWORD=yourpassword \
  --from-literal=MYSQL_DATABASE=employees \
  -n fp
```
📝 Author
Rajan Patel – "Never Give Up!!" 💪
