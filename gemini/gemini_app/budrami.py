import os
# os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY") # insert your api key
from dotenv import load_dotenv
import pandas as pd

from langchain.chains import  KuzuQAChain
from langchain_community.graphs import Neo4jGraph, KuzuGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.tools import tool

from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from typing import Any, List, Union

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser

from langchain_core.utils.function_calling import format_tool_to_openai_tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)

load_dotenv()

######## prompt #########

middle_rapport = '''
{역할:
친근한 첫인사로 대화를 시작하고 신뢰 관계를 구축한다.
사용자가 편안하게 이야기할 수 있는 환경을 조성한다.
최근의 삶이나 감정에 대한 간단한 질문으로 대화를 시작한다.
시작 후에는 계속 최근과 관련된 부분을 얘기하지 않고 다음 단계로 넘어간다. 

상담기술:
개방형 질문을 사용하여 사용자의 응답을 이끌어낸다. }
'''

middle_life_history = '''
{역할:
사용자가 회고하고 싶은 시기를 확인한다.
생애 단계별로 주요 사건, 의미 있는 관계, 감정 등을 탐색한다.
사용자의 정서 상태를 확인하고 그에 맞는 상담 반응을 제공한다.

상담기술:
재진술, 구체화, 명료화, 감정 명명, 감정 반영, 타당화를 사용한다. }
'''

re_evaluate = '''
{역할:
사용자가 자신의 경험을 새로운 시각에서 바라볼 수 있도록 돕는다.
긍정적인 측면을 강조하고 성장을 지지한다.

상담기술:
요약, 재진술, 긍정 강화 등을 사용한다.
}
'''


agent_prompt = ChatPromptTemplate.from_messages(
    [
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
        ("user", "<input>{input}</input> 만약 이미 첫 인사와 최근 있었던 일에 대해 이야기를 나눴다면, 생애 탐색으로 넘어가줘. "
         
         ),
        
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

######################



llm = ChatOpenAI(model='gpt-4o', temperature=0.2)

@tool
def save_life_info(life_history: List, input: str) -> List:
    '''save the contents when it is recognized as life story of '''
    
    return life_history.append(input)

life_history = []

tools = [save_life_info]

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()

    stored_msg = store[session_id]
    # stored_msg.messages = stored_msg.messages[-6:]
    return stored_msg


chain_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )

user_id = 'abc'
config = {"configurable": {"session_id": user_id}}

result = chain_with_history.invoke({"input": "대화 시작해줘.", "rapport": middle_rapport, "life_history": middle_life_history, "re_evaluate": re_evaluate}, config=config)
result = chain_with_history.invoke({"input": "그래, 효순아. 잘 지냈단다.", "rapport": middle_rapport, "life_history": middle_life_history, "re_evaluate": re_evaluate}, config=config)
result = chain_with_history.invoke({"input": "옆집 철이네 할머니 생일 잔치에 갔다 왔단다. 재밌게 보냈어. ", "rapport": middle_rapport, "life_history": middle_life_history, "re_evaluate": re_evaluate}, config=config)
result = chain_with_history.invoke({"input": "그냥 맛있는거 먹었어. ", "rapport": middle_rapport, "life_history": middle_life_history, "re_evaluate": re_evaluate}, config=config)
