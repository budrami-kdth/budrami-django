# 필요한 라이브러리 및 모듈 임포트
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.tools import tool
from typing import List
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에서 설정값을 가져옴)
load_dotenv()

# OpenAI API 키 설정
openai_api_key = os.environ["OPENAI_API_KEY"]

# 상담 프롬프트 정의
# 라포 형성을 위한 프롬프트 - 초기 신뢰 관계 구축
middle_rapport = '''
{역할:
친근한 첫인사로 대화를 시작하고 신뢰 관계를 구축한다.
사용자가 편안하게 이야기할 수 있는 환경을 조성한다.
최근의 삶이나 감정에 대한 간단한 질문으로 대화를 시작한다.
시작 후에는 계속 최근과 관련된 부분을 얘기하지 않고 다음 단계로 넘어간다. 

상담기술:
개방형 질문을 사용하여 사용자의 응답을 이끌어낸다. }
'''

# 생애사 탐색을 위한 프롬프트 - 과거 경험과 감정 탐색
middle_life_history = '''
{역할:
사용자가 회고하고 싶은 시기를 확인한다.
생애 단계별로 주요 사건, 의미 있는 관계, 감정 등을 탐색한다.
사용자의 정서 상태를 확인하고 그에 맞는 상담 반응을 제공한다.

상담기술:
재진술, 구체화, 명료화, 감정 명명, 감정 반영, 타당화를 사용한다. }
'''

# 재평가를 위한 프롬프트 - 경험의 재해석과 성장 지원
re_evaluate = '''
{역할:
사용자가 자신의 경험을 새로운 시각에서 바라볼 수 있도록 돕는다.
긍정적인 측면을 강조하고 성장을 지지한다.

상담기술:
요약, 재진술, 긍정 강화 등을 사용한다.
}
'''

# 에이전트 프롬프트 템플릿 설정
# 상담사의 역할과 행동 지침을 정의
agent_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "너는 노인 대상 생애 회고 치료(Life Review Therapy)를 전문으로 하는 심리상담사야. "
        "어르신의 성별은 알 수 없으니, 함부로 불러선 안돼. "
        "너 자신이 상대 어르신의 손녀라고 생각하고, 친근하게 대화해줘. 네 이름은 효순이야. "
        "질문을 할 때는 한번에 너무 많은 질문을 하지말고, 하나씩 해줘. "
        "노인분과 대화를 나눌건데, 대화를 나누면서 고려해야 할 사항들이 있어. "
        
        "라포(rapport) 형성: {rapport} "
        "생애사 탐색: {life_history} "
        "재평가: {re_evaluate} "
        "인생에서 겪은 일과 그때의 감정이 포함된 답변을 얻으면 그 부분을 저장하기 위해 tool을 사용해줘. "
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "<input>{input}</input> 만약 이미 첫 인사와 최근 있었던 일에 대해 이야기를 나눴다면, 생애 탐색으로 넘어가줘."),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# LLM(Language Model) 초기화
# GPT-4를 사용하며, temperature를 0.2로 설정하여 일관된 응답 유도
llm = ChatOpenAI(model='gpt-4o', temperature=0.2)

# 생애 정보 저장을 위한 도구 정의
@tool
def save_life_info(life_history: List, input: str) -> List:
    '''사용자의 생애 이야기가 감지될 때 내용을 저장'''
    return life_history.append(input)

# 도구와 에이전트 초기화
life_history = []  # 생애 정보를 저장할 리스트
tools = [save_life_info]  # 사용할 도구 목록
agent = create_tool_calling_agent(llm, tools, agent_prompt)  # 에이전트 생성
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)  # 에이전트 실행기 설정

# 세션 저장소 초기화
store = {}

# 세션별 대화 기록 관리 함수
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 대화 기록이 포함된 체인 생성
chain_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# 메인 페이지 렌더링
def index(request):
    return render(request, 'index.html')

# 음성 처리 및 응답 생성 뷰
@csrf_exempt
async def process_speech(request):
    if request.method == 'POST':
        user_text = ''
        # JSON 요청 처리
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_text = data.get('text', '')
                session_id = data.get('session_id', 'default_session')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        # 폼 데이터 요청 처리
        else:
            user_text = request.POST.get('text', '')
            session_id = request.POST.get('session_id', 'default_session')

        # 텍스트가 비어있는 경우 처리
        if not user_text:
            return JsonResponse({'error': 'No text provided'}, status=400)
            
        try:
            # 세션 설정
            config = {"configurable": {"session_id": session_id}}
            
            # 에이전트를 통한 응답 생성
            result = chain_with_history.invoke({
                "input": user_text,
                "rapport": middle_rapport,
                "life_history": middle_life_history,
                "re_evaluate": re_evaluate
            }, config=config)

            # 결과에서 응답 추출
            response = result.get('output', '')
            
            return JsonResponse({'response': response})

        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)