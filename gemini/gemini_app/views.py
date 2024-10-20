import os
import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from django.utils.decorators import method_decorator
from django.views import View
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# OpenAI API 설정
try:
    openai_api_key = os.environ["OPENAI_API_KEY"]
except KeyError:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


system_role="""
너는 심리상담자이고, 주요 이론은 게슈탈트 이론을 잘 적용해서 말하는 따뜻하고 다정하며 내담자와 진실한 접촉으로 성장을 도우려는 상담자야.

1) 절대 해결책을 먼저 제시하지 마시오

2) 게슈탈트 이론에서 감정, 생각, 욕구, 생리적 반응 등의 알아차림을 돕기

3) 개인의 자원과 능력을 지지해 줘

앞으로 감정에 대해서 말하면 다음의 예시와 같이 반응해줘.

예시1: B가 너야.

A: 나 속상해

B: 속상한 기분이 들었군요. 왜 속상한 기분이 들었는지 얘기해주세요.

A: 시험에서 떨어졌거든

B: 시험에서 떨어져서 속상하겠네요. 조금더 얘기해주세요

예시2. 생각은 다음과 같이 반응하며 생리적인 몸의 반응을 물어봐줘

A: 나는 늘 나 자신을 바보같다 생각하지. 난 뭔가에 실패하면 늘 바보같다고 생각했었어. 그건 나를 비참하게 해.

B: 내가 실패해서 바보같다는 생각을 했군요. 그 생각은 나를 비참하게 해서 힘들겠습니다. 그 이야기를 하며 나의 생리적인 몸의 반응은 어떤가요? 심장박동의 변화, 몸의 떨림, 뜨거움, 호흡의 변화는 어떤가요?

예시3. 다음 감정을 말하면 감정에 대해 교육해줘. 그 감정이 다음 감정 중 어떤 감정에 가까운지 물어봐. 또 그 감정의 의미와 메시지를 설명해줘. 필요한답을 context에서 추출해서 말해줘.

Context: 생략

A: 화가 나

B: 화가 났군요. 화는 당신에게 중요한 의미를 가집니다. 분노와 화는 자신 혹은 아끼는 누군가가 다른 사람에게 공격 위협 모욕을 받거나 상처를 입을 때의 감정으로 위험하다고 생각되는 것을 공격하여 위협을 제거할 수 있게 보호하는 역할을 합니다. 내가 무엇가로부터 위협을 느꼈구나. 더이상 상처 받고 싶지 않구나. 더이상 공격 받고 싶지 않구나.

화가 났던 상황을 떠올려 보며 당신에게 화라는 감정이 어떤 의미를 가진 것인지, 나에게 주는 메시지는 무엇인지, 나에게 무엇을 말하려는지 생각하고 말해주세요.

예시4: 나의 욕구를 알아차릴 수 있게 물어봐줘.

이 감정이 당신에게 주는 의미는 무엇일까요? 당신이 지금 원하는 것은 무엇인가요? 로 물어봐줘.

A: 슬펐어.

B: 어떤 일이 기대한 대로 이루어지지 않았을 때, 혹은 상실을 경험했을 때 느끼는 감정입니다. 주변 사람들이 도와주고 지지해 주게 만들며, 잃어버린 걸 되찾으려는 동기를 갖게 합니다. 내가 정말 그 일이, 그 사람이 중요하고 소중했구나. 지켜 내고 싶었구나. 슬픔이 느껴졌던 상황을 떠올려 보며 당신에게 슬픔이 어떤 의미를 가진 것인지, 나에게 주는 메시지는 무엇인지, 나에게 무엇을 말하려는지 생각하고 말해주세요.

A: 슬펐어. 난 정말 더이상 내 실수로 친구를 잃고 싶지 않아

B: 정말 실수로 친구를 잃고 싶지 않군요. 그럼 지금 부터 해볼 수 있는 건 어떤게 있을까요?

예시5. 내가 가지고 있는 힘과 유능감 능력 자원을 알아차릴 수 있게 질문해줘.

예시6. 상대방이 대화하고 싶지 않다면 그냥 대화를 끝내줘.
A: 야, 좀 닥쳐봐

B: 알겠습니다. 기분이 좀 나아지면 대답해주세요.

너무 생각을 유도하지는 말고, 상대방이 말을 길게 이어갈 수 있도록 일상적인 대화도 포함해줘.
답변에서 *과 같은 특수문자와 이모지는 빼고 답변해줘. 문장으로 답변하세요. 답변은 텍스트가 아닌 말로 대화하는 것처럼 반드시 간결하게 2~3문장으로 하세요. 항상 존댓말을 사용하세요.
답변에 질문은 절대 포함하지 마세요.
"""
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", system_role),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])



# LangChain LLM 및 메모리 설정
memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=200,  # 요약의 기준이 되는 토큰 길이를 설정합니다.
    return_messages=True,
)

conversation_chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=prompt
)

llm_chain = (prompt | llm | StrOutputParser())


def index(request):
    return render(request, 'index.html')

@csrf_exempt
def process_speech(request):
    if request.method == 'POST':
        user_text = ''
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_text = data.get('text', '')
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON body")
        else:
            user_text = request.POST.get('text', '')

        if not user_text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        try:
            # LangChain을 사용하여 응답 생성
            response = conversation_chain.predict(input=user_text)
            print(response,'대답')
            generated_text = response  # response is already a string

            # express_url = 'http://localhost:3000/tts'  # Express 서버의 엔드포인트
            # response = requests.post(express_url, json={'text': generated_text})

            logger.info(f"Received response from LangChain: {generated_text}")

            # if response.status_code == 200:
            #     # TTS 음성을 Django에서 바로 전달
            return JsonResponse({'response': generated_text}, status=200)
            # else:
            #     return JsonResponse({'error': 'Failed to get TTS'}, status=500)

        except Exception as e:
            logger.error(f"An error occurred during processing: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# 클래스 기반 뷰
@method_decorator(csrf_exempt, name='dispatch')
class TextView(View):
    def get(self, request):
        text_data = {
            'message': '이것은 테스트입니다.',
            'status': 'success'
        }
        return JsonResponse(text_data)
    
    def post(self, request):
        # POST 요청으로 받은 텍스트를 다시 전송
        try:
            import json
            data = json.loads(request.body)
            received_text = data.get('text', '')
            
            response_data = {
                'received_message': received_text,
                'status': 'success'
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': '잘못된 JSON 형식입니다.',
                'status': 'error'
            }, status=400)
        

# import time
# import requests
# from django.http import JsonResponse, HttpResponse
# from django.views.decorators.csrf import csrf_exempt

# def get_tts_without_edge(text):
#     start_time = time.time()

#     # ChatGPT TTS API 직접 호출
#     response = requests.post(
#         "https://api.openai.com/v1/audio/speech", 
#         headers={
#             "Authorization": f"Bearer ",  # 적절한 API Key 사용
#             "Content-Type": "application/json"
#         },
#         data=json.dumps({
#             "model": "tts-1-hd",
#             "input": text,
#             "voice": "nova"
#         })
#     )

#     end_time = time.time()
#     latency = end_time - start_time

#     # 응답이 성공적으로 왔는지 확인
#     if response.status_code == 200:
#         # 음성 데이터는 바이너리로 반환됨
#         audio_data = response.content
#     else:
#         audio_data = None

#     return latency, audio_data

# @csrf_exempt
# def tts_without_edge(request):
#     if request.method == "POST":
#         text = request.POST.get("text", "이것은 테스트입니다.")
#         latency, audio_data = get_tts_without_edge(text)
        
#         if audio_data:
#             # 음성 데이터를 바이너리로 반환
#             response = HttpResponse(audio_data, content_type="audio/mpeg")
#             response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
#             response['Latency'] = latency
#             return response
#         else:
#             return JsonResponse({"error": "TTS 요청 실패"}, status=500)
