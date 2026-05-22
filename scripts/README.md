# GitHub Actions Self-Hosted Runner

Setup runner trên Windows để chạy workflow `retrain` mà không cần GitHub-hosted minutes.

## 1. Lấy token đăng ký

1. Vào: https://github.com/coderiukl/rt-video-learning-analytics/settings/actions/runners/new
2. Chọn **Windows** + **x64**
3. Copy giá trị `--token` (chuỗi dạng `ABCDEF123...`)

> Token có hạn 1 giờ — nếu hết hạn, vào lại trang trên lấy token mới.

## 2. Cài runner

Mở **PowerShell as Administrator**:

```powershell
cd D:\rt-video-learning-analytics
.\scripts\install-github-runner.ps1 -Token "PASTE_TOKEN_HERE"
```

Tham số tùy chọn:

```powershell
.\scripts\install-github-runner.ps1 `
    -Token "..." `
    -InstallPath "D:\actions-runner" `
    -RunnerName "ml-runner-01" `
    -Labels "self-hosted,windows,x64,ml"
```

Script sẽ:
- Download runner v2.319.1
- Configure registration
- Install + start Windows service (auto-start cùng máy)
- Verify status

## 3. Verify

```powershell
Get-Service "actions.runner.*"
```

Hoặc UI: Settings → Actions → Runners → status 🟢 **Idle**.

## 4. Trigger workflow

```powershell
# Chạy ngay (tận dụng cache DVC)
.\scripts\run-workflow.ps1

# Force rerun toàn bộ
.\scripts\run-workflow.ps1 -Force

# Trigger + watch log realtime
.\scripts\run-workflow.ps1 -Watch
```

Hoặc UI: Repo → Actions → retrain → Run workflow.

## 5. Quản lý runner

```powershell
cd D:\actions-runner

# Stop service
.\svc.cmd stop

# Start service
.\svc.cmd start

# Uninstall service (giữ runner)
.\svc.cmd uninstall

# Xóa runner khỏi GitHub
.\config.cmd remove --token <NEW_REMOVE_TOKEN>
```

## Troubleshoot

| Triệu chứng | Nguyên nhân | Fix |
|---|---|---|
| Job kẹt "Waiting for a runner" | Service chưa start | `.\svc.cmd start` |
| `dvc: command not found` | PATH chưa load | Reboot máy hoặc restart service |
| `Python not found` | actions/setup-python cần internet | Check firewall |
| Service không start | Quyền user | Cài lại với account khác qua `svc.cmd install <DOMAIN\user>` |
| Log lỗi chi tiết | — | Xem `D:\actions-runner\_diag\` |

## Cấu hình bổ sung (DVC remote)

Nếu workflow cần push/pull DVC Gdrive remote, runner phải có credentials:

```powershell
# Trên máy chạy runner
$env:GDRIVE_CREDENTIALS_DATA = Get-Content C:\path\to\gdrive-sa.json -Raw
dvc remote modify --local origin gdrive_use_service_account true
```

Hoặc set `GDRIVE_CREDENTIALS_DATA` trong **Repo Settings → Secrets → Actions** — workflow sẽ tự inject.
