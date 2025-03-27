# wineandnews-api
* Wine & News WEB API


## How to run in local
```bash
    git clone -b develop --single-branch https://github.com/metric-studio/wineandnews-api
    cd wineandnews-api
    virtualenv venv --python=python3.9
    . venv/bin/activate
    pip3 install -r requirements.txt
    chalice local --stage {dev/prod}
```

## How to deploy in local
```bash
    git clone -b develop --single-branch https://github.com/metric-studio/wineandnews-api
    cd wineandnews-api
    virtualenv venv --python=python3.9
    . venv/bin/activate
    pip3 install -r requirements.txt
    chalice deploy --stage {dev/prod}
```

## How to test in local
```bash
    git clone -b develop --single-branch https://github.com/metric-studio/wineandnews-api
    cd wineandnews-api
    virtualenv venv --python=python3.9
    . venv/bin/activate
    pip3 install -r requirements.txt
    py.test tests/v2/articles.py
```


## History Log

#### 2024-05-03
* Wine&News v1.3 QA사항 반영
* Wine&News v1.2 deprecate (remove code)

#### 2024-04-29
* User Authorization 방식 변경: Set-Cookie -> Authorization Bearer Token
* Response metadata 추가: Location & Language 반환
* Wine 상세 - infoDescription 추가 / Pairing 중복 제거

#### 2024-04-22
* API V1.3 버전 마이그레이션 완료

#### 2024-03-27
* 서버 이전: KR Seoul -> US Virginia

#### 2024-03-18
* User Authorization 방식 변경: Set-Cookie
* Update Article Reaction API V1.2 upgrade
* Subscription APIs V1.2 upgrade

#### 2024-03-14
* User API V1.2 추가

#### 2024-03-13
* Comments API V1.2 추가