import os

one_api_key = os.getenv("ONE_API_KEY","Python666good@")
one_api_url = os.getenv("ONE_API_URL", "https://oneapi.wlove.top/v1")
model_name = os.getenv("MODEL_NAME", "gpt-4.1")
temperature = os.getenv("TEMPERATURE", 0.7)


from langchain_openai import ChatOpenAI
from langchain.agents import create_agent, AgentState
llm = ChatOpenAI(
    model=model_name,
    temperature=temperature,
    openai_api_key=one_api_key,
    base_url=one_api_url,


)
agent = create_agent(
    llm,
    system_prompt="你是我的人工智能助手，协助我解答问题和提供信息。请根据用户的提问，尽可能准确和详细地回答。如果你不确定答案，可以说你不知道，但请尽量提供相关的信息或建议。"
)

if __name__ == '__main__':
    print(agent.invoke({"messages":[{"role":"user","content":"你好"}]}))
