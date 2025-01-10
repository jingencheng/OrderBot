from agents_qwen import AgentV1, OrderBotAgentV1, JsonSummaryAgentV1
from agents_qwen import AgentV2, OrderBotAgentV2, JsonSummaryAgentV2, DecisionMakerAgentV2
from utils import CodeExtractor, JsonLoader, JsonReader, YesNoExtractor

import time



# 点餐程序 v1 支持多线程
def main_v1(): 
    print("\n\nWelcome to OrderBot System\n\n* two agents collaborated \n* diy menu in prompts.py \n* monitor_script.py tracking \n\n* next or quit by command: done666\n\n")

    ce = CodeExtractor() # json提取工具

    ai = OrderBotAgentV1() # 主agent 支持user与llm多轮携带记忆的交互
    jsa = JsonSummaryAgentV1() # 副agent 对于user与llm的交互历史纪录做Json总结

    jl = JsonLoader(database='order.json') # 录入数据库工具
    jr = JsonReader(database='order.json') # 读取数据库工具

    print("\n\nbot: \n\n")
    ai.chat("Hello")
    while True:
        Qn = input("\n\nuser: \n\n\n")
        if Qn == "done666": # 神秘代码： 换人 或者 退出程序
            
            # 使用主agent的全部历史messages 请求json summary (模型有时候没有预期回答 导致下面的json提取失败！！)
            hcr = jsa.hidden_chat_return(ai.messages) # hidden_chat_return 请求agent jsa

            # 读取数据库order
            order = jr.read()
            # 把 订单 or 最后一条消息 加进order
            order.append(ce.extract(hcr)) # 使用另一个agent总结 注意：如果总结有误 会把jsa的回复append到order里

            # 导回更新后的order进入数据库
            jl.load(order)

            Qn = input("\n\nThanks for your order\n1. quit\n2. next order\n\n")
            if Qn == "1" or Qn == "quit":
                break

            # 初始化即清除历史纪录 给下个人继续用 (保留前两个 因为system的content定义了1个)
            ai.messages = ai.messages[:1]
            Qn = "Hello" # 作为下一个人的开头
        print("\n\nbot: \n\n")
        ai.chat(Qn)


# 点餐程序 v2 支持多线程
def main_v2():
    print("\n\nWelcome to OrderBot System\n\n* two agents collaborated \n* diy menu in prompts.py \n* monitor_script.py tracking \n\n* next or quit by command: done666\n\n")

    ce = CodeExtractor() # json提取工具

    ai = OrderBotAgentV2() # 主agent 支持user与llm多轮携带记忆的交互
    jsa = JsonSummaryAgentV2() # 副agent 对于user与llm的交互历史纪录做Json总结

    jl = JsonLoader(database='order.json') # 录入数据库工具
    jr = JsonReader(database='order.json') # 读取数据库工具

    print("\n\nbot: \n\n")
    ai.chat("Hello")
    while True:
        Qn = input("\n\nuser: \n\n\n")
        if Qn == "done666": # 神秘代码： 换人 或者 退出程序
            
            # 使用主agent的全部历史chat_history(除了system content) 请求json summary (模型有时候没有预期回答 导致下面的json提取失败！！)
            hcr = jsa.hidden_chat_return(ai.chat_history[1:]) # hidden_chat_return 请求agent jsa

            # 读取数据库order
            order = jr.read()
            # 把 订单 or 最后一条消息 加进order
            order.append(ce.extract(hcr)) # 使用另一个agent总结 注意：如果总结有误 会把jsa的回复append到order里

            # 导回更新后的order进入数据库
            jl.load(order)

            Qn = input("\n\nThanks for your order\n1. quit\n2. next order\n\n")
            if Qn == "1" or Qn == "quit":
                break

            # 初始化即清除历史纪录 给下个人继续用 (保留前两个 因为system的content定义了1个)
            ai.messages = ai.messages[:1]
            ai.chat_history = ai.chat_history[:1] # chat_history也要清除一下
            Qn = "Hello" # 作为下一个人的开头
        print("\n\nbot: \n\n")
        ai.chat(Qn)



def main_v3():
    print("\n\nWelcome to OrderBot System\n\n* two agents collaborated \n* diy menu in prompts.py \n* monitor_script.py tracking \n\n* next or quit by command: done666\n\n")

    ce = CodeExtractor() # json提取工具

    ai = OrderBotAgentV2() # 主agent 支持user与llm多轮携带记忆的交互
    jsa = JsonSummaryAgentV2() # 副agent 对于user与llm的交互历史纪录做 Json总结
    dm = DecisionMakerAgentV2() # 副agent 对于user与llm的交互历史记录做 结单判断

    jl = JsonLoader(database='order.json') # 录入数据库工具
    jr = JsonReader(database='order.json') # 读取数据库工具
    yn = YesNoExtractor() # Yes/No 提取工具

    print("\n\nbot: \n\n")
    ai.chat("Hello")
    while True:
        print("\n可否结单: \n")        
        hdr = dm.hidden_decision_return(ai.chat_history[1:])
        print(hdr)
        print(yn.extract(hdr))
        Qn = input("\n\nuser: \n\n\n")
        if Qn == "done666": # 神秘代码： 换人 或者 退出程序
            
            # 使用主agent的全部历史chat_history(除了system content) 请求json summary (模型有时候没有预期回答 导致下面的json提取失败！！)
            hcr = jsa.hidden_chat_return(ai.chat_history[1:]) # hidden_chat_return 请求agent jsa

            # 读取数据库order
            order = jr.read()
            # 把 订单 or 最后一条消息 加进order
            order.append(ce.extract(hcr)) # 使用另一个agent总结 注意：如果总结有误 会把jsa的回复append到order里

            # 导回更新后的order进入数据库
            jl.load(order)

            Qn = input("\n\nThanks for your order\n1. quit\n2. next order\n\n")
            if Qn == "1" or Qn == "quit":
                break

            # 初始化即清除历史纪录 给下个人继续用 (保留前两个 因为system的content定义了1个)
            ai.messages = ai.messages[:1]
            ai.chat_history = ai.chat_history[:1] # chat_history也要清除一下
            Qn = "Hello" # 作为下一个人的开头
        print("\n\nbot: \n\n")
        ai.chat(Qn)




def test():
    dm = DecisionMakerAgentV2()
    hdr = dm.hidden_decision_return([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "what can i help you today?"},
        {"role": "user", "content": "any recommendations?"},
        {"role": "assistant", "content": "we offer pizzas and sides"},
    ])
    print(hdr)

if __name__ == "__main__":
    main_v2()
    

    

    
    

