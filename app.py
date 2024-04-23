from fastapi import Request, FastAPI, BackgroundTasks
import gspread
import requests


# Chatbase API를 이용해 텍스트를 보내고 응답을 받는 함수
def getResponseFromChatbase(prompt):
    url = "https://www.chatbase.co/api/v1/chat"
    payload = {
        "stream": False,
        "temperature": 0,
        "chatId": "6dMpdT5zPPS5ik9pKptsH",
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer e81b355c-30cc-47ca-b9fa-deb33f7159ad"
    }
    response = requests.post(url, json=payload, headers=headers)
    # Chatbase API 응답의 형태에 따라 적절한 필드를 반환
    # {"text":"안녕하세요! 이나라도움 AI입니다. 어떤 도움이 필요하신가요?"}
    return response.json()['text']


# 메세지 전송을 위한 포맷 함수
def textResponseFormat(bot_response):
    response = {
        'version': '2.0',
        'template': {
            'outputs': [{"simpleText": {"text": bot_response}}],
            'quickReplies': []
        }
    }
    return response
    propert

def create_callback_request_kakao(prompt, callbackUrl):
    # OpenAI API로 prompt를 던져서 결과를 받아옵니다.
    bot_res = getResponseFromChatbase(prompt)

    # callbackUrl로 결과값을 post방식으로 전송합니다.
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    requests.post(
        callbackUrl,
        json=textResponseFormat(bot_res),
        headers=headers,
        timeout=5
    )
    return ""


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()


# 백그라운드 처리: verymuchmorethanastronomically.tistory.com/18 참고.
@app.post("/chat2/", tags=["kakao"])
async def chat2(request: Request, background_tasks: BackgroundTasks,):
    # await 처리하지 않으면 userRequest를 읽다가 에러가 발생됩니다.
    kakao_request = await request.json()

    # /ask, /img, /gs 처리.
    if '/gs' in kakao_request["userRequest"]["utterance"]:
        question = kakao_request["userRequest"]["utterance"].replace("/gs", "")
        # json 파일이 위치한 경로를 값으로 줘야 합니다.
        json_file_path = "botree-404708-b377977f1aa4.json"
        gc = gspread.service_account(json_file_path)
        sheet = 'https://docs.google.com/spreadsheets/d/'\
                '1Iq5N59xU725bmxas730B_UQYZvX4EK_0rnRL-egxl_I/edit?usp=sharing'
        doc = gc.open_by_url(sheet)
        worksheet = doc.worksheet("시트1")

        # 이전에 입력된 데이터가 있는 경우 마지막 행을 찾아서 다음 행에 데이터를 추가
        last_row = len(worksheet.col_values(1)) + 1
        cell = f'A{last_row}'

        # 사용자가 챗봇에 입력한 값을 해당 열에 넣어줍니다.
        worksheet.update(cell, question)
        return textResponseFormat(f"{cell}에 작성 완료.")

    # 텍스트의 길이가 10자 이상 200자 이하인지 확인
    length = len(kakao_request["userRequest"]["utterance"])
    if length < 5 or length > 200:
        return textResponseFormat("질문은 5자 이상 200자 이하로 입력해주세요")

    # 백그라운드로 카카오 챗봇에게 응답을 보냅니다.
    background_tasks.add_task(
        create_callback_request_kakao,
        prompt=kakao_request["userRequest"]["utterance"].replace("/ask", ""),
        callbackUrl=kakao_request["userRequest"]["callbackUrl"],
    )

    # user_requests[user_id] += 1
    # useCallback을 true처리해줘야 카카오에서 1분간 callbackUrl을 유효화시킵니다.
    return {"version": "2.0", "useCallback": True}
