오늘 실습 내용을 기록

# Week 11 실습

## 오늘 한 것
- PyInstaller 설치 및 빌드
- resource_path() 함수 추가
- --add-data 옵션으로 에셋 포함
- .exe 실행 확인

## resource_path() 를 써야 하는 이유
- resource_path 사용하지 않으면 파일의 주소를 찾을 수가 없어서 에셋 파일이 있더라도 정상적으로 이미지,폰트,사운드가 출력되지 않는다.

## 빌드 명령어
- pyinstaller --onefile --windowed --add-data "assets;assets"  --name=MyGame week11.py
- pyinstaller week11.py

## AI 활용 내역
- resource_path를 적용 시키는데 사용함
- resource_path 역할을 확인하는데 사용함