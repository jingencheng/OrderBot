from huggingface_hub import InferenceClient
from prompts import huggingface_api, orderbot_system_content, orderbot_json_summary_request, orderbot_json_summary_system_content

# messages 中的 role keys
# system: 
# 介绍背景 即扮演角色说明
# user: 
# 提出需求 可携带信息作为提示词 进行交互



# 开发时间: 2024.12.05 ~ 2024.12.11 
# Multi-Turn Interaction - Messages Appending
# 两个agents协作
# 主要缺陷：
# 1. 很容易出现LLM意外模拟user输出：
# 下面class Agent中提出了一种简单的解决方法 以'user'为记号 定义记号后的内容均属于意外输出 从而删除
# 2. 如果对话记录冗长 将消耗大量tokens
# 虽然user与点单bot的交互纪录一般来说不会太长 但是还是会有一些无用的废话 可以使用提示词做适当的总结

# 父类
class AgentV1:
    def __init__(self, model="Qwen/QwQ-32B-Preview", messages=[], role='assistant', prompt='', text_description=''):
        self.messages = [{"role": "system", "content": f"""You are an experienced {role}."""}]
        self.prompt = prompt
        self.text_description = text_description
        self.role = role
        self.model = model

    def chat(self, text):
        client = InferenceClient(api_key=huggingface_api) # token

        # 把user的提问纪录在messages里面
        if self.prompt == '':
            self.messages.append({"role": "user", "content": f"""{text}"""})
        else:
            self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: ```{text}``` """})

        # 带着messages去交互
        stream = client.chat.completions.create(
			model=self.model, # "Qwen/Qwen2.5-Coder-32B-Instruct", 
			messages=self.messages, 
			max_tokens=5000,
			stream=True
		)
        
        communication = ''
        for chunk in stream:
            # print(chunk.choices[0].delta.content, end="") 流式输出
            # 存一下output
            communication += chunk.choices[0].delta.content
        
        # 有一个标准 避免意外user输出 一般模型会用\nuser开头
        # 所以这里要预处理一下communication
        if 'user' in communication: # 检查一下有没有这个标志性错误
            communication = communication.split('user')[0]
        # 这里处理了assistant‘s content不会有意外user输出 保护messages信息
        print(communication)
        
        # 把qwen的回复记录在messages里面
        self.messages.append({"role": "assistant", "content": f"""{communication}"""})


    
    def get_last_message(self):
        return self.messages[-1]['content']



# 子类
# 点单系统 主agent 负责与客户对话
class OrderBotAgentV1(AgentV1):
    def __init__(self, model="Qwen/QwQ-32B-Preview"):
        super().__init__(model=model)
        self.messages = [{'role': 'system', 'content': orderbot_system_content}]
    
    def hidden_chat(self, text):
        client = InferenceClient(api_key=huggingface_api) # token
        if self.prompt == '': 
            self.messages.append({"role": "user", "content": f"""{text}"""})
        else: 
            self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: ```{text}``` """})
        stream = client.chat.completions.create(model=self.model, messages=self.messages, max_tokens=5000, stream=True)
        communication = ''
        for chunk in stream:
            communication += chunk.choices[0].delta.content
        if 'user' in communication: # 检查一下有没有这个标志性错误
            communication = communication.split('user')[0]    
        self.messages.append({"role": "assistant", "content": f"""{communication}"""})



# 点单系统 副agent 负责json总结
class JsonSummaryAgentV1(AgentV1): 
    # 无记忆能力 即无历史消息干扰
    # 单次回复json总结
    def __init__(self, model="Qwen/Qwen2.5-Coder-32B-Instruct"):
        super().__init__(model=model)
        self.role = 'coder'
        self.prompt = f"""Based on the messages given. {orderbot_json_summary_request}"""
        self.text_desciption = 'messages'

    def hidden_chat_return(self, text):
        client = InferenceClient(api_key=huggingface_api) # token
        self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: {text} """})
        stream = client.chat.completions.create(model=self.model, messages=self.messages, max_tokens=5000, stream=True)
        communication = ''
        for chunk in stream:
            communication += chunk.choices[0].delta.content
        if 'user' in communication: # 检查一下有没有这个标志性错误
            communication = communication.split('user')[0]    
        return communication





############################## 更新 ##############################
# 开发时间: 2024.12.11 ~ 2024.12.12
# Multi-Turn Interaction - Memory Prompting (New)
# 依旧 两个agents协作
# 修复了V1版本LLM意外模拟user的输出bug (改为非流式输出)
# 主要缺陷: 
# 1. 依旧需要手动输入done666来结单(详情参考main.py里面的main_v1()和main_v2()):
# v3会加入第三个agent来判断对话是否可以结束 预估实现功能: 
# i. 追问user 如果订单不完整并且time.sleep(?)后没回复 继续等待...
# ii. 追问user 如果订单完整并且time.sleep(?)后没回复 agent帮助user输出done666来结单 

# 父类
class AgentV2:
    def __init__(self, model="Qwen/QwQ-32B-Preview", messages=[], role='assistant', prompt='', text_description='user'):
        self.messages = [{"role": "system", "content": f"""You are an experienced {role}."""}] # 与模型交互的属性 一次性交互
        self.chat_history = [{"role": "system", "content": f"""You are an experienced {role}."""}] # 存储干净的user与assistant的记录
        self.prompt = prompt # 变量 因为声明聊天记录中chat_history是变量
        self.original_prompt = prompt # 不变量
        self.text_description = text_description
        self.role = role
        self.model = model

    def chat(self, text):
        client = InferenceClient(api_key=huggingface_api) # token

        # 把user的提问纪录在messages里面
        if self.prompt == '':
            self.messages.append({"role": "user", "content": f"""{text}"""})
        else:
            self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: {text} """})
        
        # 把user的提问存入chat_history
        self.chat_history.append({"role": "user", "content": f"""{text}"""})

        # 带着messages去交互 并得到model的回复
        response = client.chat.completions.create(model=self.model, messages=self.messages, max_tokens=5000, stream=False)
        # communication = ''
        # for chunk in stream:
        #     communication += chunk.choices[0].delta.content
        communication = response['choices'][0]['message']['content']

        # 把回复追加到chat_history list里面
        self.chat_history.append({"role": "assistant", "content": f"""{communication}"""})

        # 把 chat_history 拼接到 原始的prompt前面 作为 新的prompt
        self.prompt = "".join([f"""Respond concisely with only the Assistant's reply based on the following conversation history: {self.chat_history}""", self.original_prompt])

        # 清空messages属性中的user聊天记录
        self.messages = self.messages[:1]

        print(communication)

# 子类
# 点单系统 主agent 负责与客户对话
class OrderBotAgentV2(AgentV2):
    def __init__(self, model="Qwen/QwQ-32B-Preview"):
        super().__init__(model=model)
        self.messages = [{'role': 'system', 'content': orderbot_system_content}]


# 点单系统 副agent 负责json总结
class JsonSummaryAgentV2(AgentV2): 
    # 无记忆能力 即无历史消息干扰
    # 单次回复json总结
    def __init__(self, model="Qwen/Qwen2.5-Coder-32B-Instruct"):
        super().__init__(model=model)
        self.role = 'coder' # 这行无用
        self.prompt = f"""Based on the provided chat history between the user and the assistant. {orderbot_json_summary_request}"""
        self.text_desciption = 'chat_history'
        self.messages = [{"role": "system", "content": orderbot_json_summary_system_content}]

    def hidden_chat_return(self, text):
        client = InferenceClient(api_key=huggingface_api) # token
        self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: {text} """})
        response = client.chat.completions.create(model=self.model, messages=self.messages, max_tokens=5000, stream=False)   
        return response['choices'][0]['message']['content']





############################## 更新 ##############################
# 开发时间: 2024.12.13 ~ 
# Single-Turn Interaction - Decision Making (New)
# 第三个agent 结单决策者

from prompts import orderbot_decision_making_content

# 结单决策者
class DecisionMakerAgentV2(AgentV2):
    def __init__(self, model="Qwen/QwQ-32B-Preview"):
        super().__init__(model=model)
        self.prompt = f"""Based on the provided chat history between the user and the assistant. Respond only with "YES" if conditions of the system's content satisfy or "NO" otherwise. Then specify reasons in the form of ```YES/NO: reasons```."""
        self.text_description = 'chat_history'
        self.messages = [{"role": "system", "content": orderbot_decision_making_content}]

    def hidden_decision_return(self, text):
        client = InferenceClient(api_key=huggingface_api)
        self.messages.append({"role": "user", "content": f"""{self.prompt} {self.text_description}: {text}"""})
        response = client.chat.completions.create(model=self.model, messages=self.messages, max_tokens=5000, stream=False)   
        return response['choices'][0]['message']['content']
# 时常判断非常不准确
# 分段思考 先总结 再判断 可以用json来判断