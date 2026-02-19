# 1. DB에서 기존 스냅샷 데이터 전체 삭제
Write-Host "Deleting old snapshots from DB..."
docker exec gold_db psql -U hajunkim -d gold_db -c "DELETE FROM portfolio_snapshots;"

# 2. 백엔드 API를 호출하여 새로운 스냅샷 생성 (현재 업비트 잔고 기준)
Write-Host "Triggering new snapshot creation..."
Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/snapshot" -Method Post

Write-Host "Done! Please refresh the frontend."
