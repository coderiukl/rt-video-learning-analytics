# Jenkins CI/CD Setup

Luồng CI/CD hoàn chỉnh:

```
git push -> GitHub Actions (self-hosted)
              |- dvc repro (train ML)
              |- dvc push (S3 artifacts)
              |- commit dvc.lock
              `- POST /build -> Jenkins
                                  |- checkout
                                  |- dvc pull (model artifacts)
                                  |- lint + test
                                  |- build images (rt-backend, rt-frontend)
                                  |- smoke test
                                  `- write /var/jenkins_home/last-green-build
                                        |
                                        v
                                  deploy.ps1 (host)
                                        |- docker compose up -d --force-recreate
```

## 1. Build & start Jenkins

```powershell
docker compose --profile cd build jenkins
docker compose --profile cd up -d jenkins
```

Unlock:
```powershell
docker compose --profile cd exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Vào http://localhost:8080 → Install suggested plugins → tạo admin user.

## 2. Add credentials vào Jenkins

Manage Jenkins → Credentials → System → Global → Add Credentials:

### AWS credentials (cho DVC pull từ S3)
- Kind: **AWS Credentials**
- ID: `aws-dvc`
- Access Key ID: <AWS_ACCESS_KEY_ID>
- Secret Access Key: <AWS_SECRET_ACCESS_KEY>

Phải khớp `credentialsId: 'aws-dvc'` trong [Jenkinsfile](Jenkinsfile).

## 3. Tạo Pipeline job

New Item → tên `rt-video-learning-analytics` → Pipeline → OK.

Configure:
- Pipeline → Definition: **Pipeline script from SCM**
- SCM: Git
- Repository URL: `https://github.com/coderiukl/rt-video-learning-analytics`
- Branch: `*/main`
- Script Path: `jenkins/Jenkinsfile`
- **Bỏ tick** `Lightweight checkout`

Save → Build Now để test.

## 4. Tạo Jenkins API token cho GH Actions

User icon (góc phải trên) → Configure → API Token → **Add new Token** → đặt tên (vd: `gh-actions`) → copy token.

## 5. Add GitHub secrets

Repo Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `JENKINS_URL` | `http://localhost:8080` (vì train.yml chạy trên self-hosted runner cùng máy) |
| `JENKINS_USER` | username admin Jenkins |
| `JENKINS_TOKEN` | API token tạo ở bước 4 |
| `JENKINS_JOB` | `rt-video-learning-analytics` (tên job) |

## 6. Test luồng đầy đủ

### Manual test từng phần
```powershell
# Trigger train từ GH UI: Actions -> retrain -> Run workflow
# Hoặc tự push commit vào mlops/** hay backend/analytics/ml/**

# Sau khi train xong, GH Actions sẽ POST -> Jenkins
# Vào http://localhost:8080 xem build mới chạy

# Sau khi Jenkins green, deploy:
.\deploy.ps1
```

### Auto deploy (watch mode)
```powershell
.\deploy.ps1 -Watch
```

Script poll mỗi 30s, tự deploy khi có build mới.

## 7. Verify

```powershell
# Backend health
curl http://localhost:8000/health/

# Frontend
curl http://localhost:5173

# Jenkins images
docker images | findstr rt-
```

## Troubleshooting

- **Jenkins không nhận trigger từ GH**: kiểm tra firewall, secret `JENKINS_URL` chính xác, self-hosted runner đang chạy.
- **DVC pull fail**: credential `aws-dvc` chưa add hoặc sai key. Stage có `|| echo ...` nên không fail pipeline.
- **Smoke test fail**: container backend chưa healthy trong 8s → tăng `sleep` trong [Jenkinsfile](Jenkinsfile) stage `Smoke test`.
- **Deploy script không thấy build**: volume name khác → kiểm tra `docker volume ls | findstr jenkins` rồi chỉnh `$jenkinsVolume` trong [deploy.ps1](../deploy.ps1).
