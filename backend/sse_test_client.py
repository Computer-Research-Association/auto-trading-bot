import requests
import json

def stream_logs(url):
    print(f"Connecting to {url}...")
    try:
        # stream=True를 설정하여 응답을 한꺼번에 받지 않고 스트림으로 받음
        response = requests.get(url, stream=True, headers={"Accept": "text/event-stream"})
        
        # SSE 연결 확인
        if response.status_code != 200:
            print(f"Failed to connect: {response.status_code}")
            return

        print("Connected! Waiting for logs...\n")
        
        # 라인 단위로 읽기
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                
                # SSE 데이터 포맷 처리 (data: {...})
                if decoded_line.startswith("data: "):
                    data_content = decoded_line[6:] # "data: " 이후의 내용
                    try:
                        log_entry = json.loads(data_content)
                        # 로그 출력 포맷팅
                        level = log_entry.get("levelname", "INFO")
                        category = log_entry.get("category", "SYSTEM")
                        message = log_entry.get("message", "")
                        timestamp = log_entry.get("created_at", "")
                        
                        print(f"[{timestamp}] [{level}] [{category}] {message}")
                    except json.JSONDecodeError:
                        print(f"Raw data: {data_content}")
                
                # event:, id:, retry: 등 다른 SSE 필드 처리 (필요시)
                elif decoded_line.startswith("event: "):
                    print(f"--- Event: {decoded_line[7:]} ---")

    except KeyboardInterrupt:
        print("\nDisconnected by user.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # 서버 주소에 맞게 수정하세요 (기본 8000 포트)
    API_URL = "http://localhost:8000/api/logs/stream"
    stream_logs(API_URL)
