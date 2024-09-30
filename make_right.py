# 利用大预言模型，纠正一些错别字
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from llm import glm_4 as model
from langchain_text_splitters import  MarkdownTextSplitter as TextSplitter


class OutPut(BaseModel):
    output: str = Field(..., title="纠错后", description="输出纠错后的文本")


system_prompt = "你是一个优秀的文字编辑专家,能根据用户要求给出编辑后的正确文稿。"
parser = JsonOutputParser(pydantic_object=OutPut)
format_instructions = parser.get_format_instructions()

human_prompt = """
我将输入一个从pdf文档中使用OCR识别的文本，这个文本会有一些错误，请帮我纠正。
##背景知识
### pdf的目录是<title>，
"{title}"
## 要求
ocr 常见错误：识别错误 英文错误
1. 修改ocr错别字，根据上下文的语义，找到OCR识别的错别字，并把错别字修改成正确的字。例如把“买人蓝筹”修改成“买入蓝筹”。
2. 修改标题格式，一些粗体文字被识别为标题， 根据上下文语义修改为粗体，或者是二级、三级标题。
3. 如果是明确的书籍章节标题<title>,就不要修改。 例如 # 1.你知道自己的未来是什么样子的吗？001  那么这句话就不需要修改。
4. 不要输出<title>的内容。
5. 不要删除任何图片链接、更改任何格式。
5. 输出的格式为{format_instructions}

### 注意事项
1. 一定保留原文的意思，在不需要修改的部分，完全copy原文。
2. 一定要保留原文的格式，保留markdown语法，不要修改。
## 例子
下面是例子,input是原文，output是正确的字:
### 例子1
原文：媒体和专家往往提倡大家奉行长期 投资的理念，反对大家从事短期投机的活动，但是他们很难帮你区分哪一次 买人是投机。
纠错后：媒体和专家往往提倡大家奉行长期投资的理念，反对大家从事短期投机的活动，但是他们很难帮你区分哪一次买入是投机。
说明：错别字：“买人蓝筹”->“买入蓝筹”
### 例子2
原文:那么，设计的最少必要知识是什么呢？其实，只要记住两个词就可以了：\n  简洁\n  # 留白  
output:那么，设计的最少必要知识是什么呢？其实，只要记住两个词就可以了：\n  简洁\n  ## 留白  
说明：根据上下文,修改标题格式，“#”改为“##” #留白 不在<title>中，所以需要根据上下文判断，发现他是二级标题，所以修改。

### 例子3
原文：接受自己的笨拙，理解自己的笨拙，放慢速度尝试，观察哪里可以改进，反复练习，观察哪里可以进一步改进，进一步反复练习·..这是学习一切技 能的必需过程一一关键在于：  
# >尽快开始这个过程  
# >尽快度过这个过程  
现在已经没有人怀疑我的文字能力了，可在十几年前我刚开始写作的时候呢？且不说那时有没有人怀疑我的文字能力，连我自己都知道自己不怎么样。  
output：接受自己的笨拙，理解自己的笨拙，放慢速度尝试，观察哪里可以改进，反复练习，观察哪里可以进一步改进，进一步反复练习·..这是学习一切技能的必需过程一一关键在于：  
**尽快开始这个过程**
**尽快度过这个过程**
说明：修改错误标题格式，“#”改为“**” #>尽快开始这个过程 #>尽快度过这个过程 不在<title>中，所以需要根据上下文判断，发现他是粗体内容，所以修改。
### 例子4
title: 1.你知道自己的未来是什么样子的吗？001 \n2.你知道那条曲线究竟是什么吗？005
原文: # 1.你知道自己的未来是什么样子的吗？  \n 虽然我们在学生时代多次写过标题是《我的理想》的作文，虽然我们在长大过程中总是向一些我们心仪的人认真描述自己的未来，但绝大多数人事实上对自己的未来并没有一个清晰直观的认识。没办法，“未来”这个东西在我们的基本感知能力之外，反正五官是不够用的，我们不可能直接“看到未来”、“听到末来”、“摸到未来”、“闻到未来”或者“尝到未来”。  
output: # 1.你知道自己的未来是什么样子的吗？ \n 虽然我们在学生时代多次写过标题是《我的理想》的作文，虽然我们在长大过程中总是向一些我们心仪的人认真描述自己的未来，但绝大多数人事实上对自己的未来并没有一个清晰直观的认识。没办法，“未来”这个东西在我们的基本感知能力之外，反正五官是不够用的，我们不可能直接“看到未来”、“听到未来”、“摸到未来”、“闻到未来”或者“尝到未来”。  
说明：标题在title中，不需要修改。 末来->未来

## 之前修改的错误原因如下：请不要再犯类似的错误了
{reason}

## 现在帮我修改下面的内容:\n---\n
{input}
"""

human_prompt_template = PromptTemplate(
    template=human_prompt,
    input_variables=['title', 'input'],
    partial_variables={"format_instructions": format_instructions}
)


@retry(stop=stop_after_attempt(3))
def make_right(title, input_text, reason=""):
    parser_model = model | parser
    out = parser_model.invoke(
        [
            SystemMessage(f"{system_prompt}"),
            human_prompt_template.format(title=title, input=input_text, reason=reason),
        ]
    )
    OutPut.validate(out)
    return out['output']


class JudgeResult(BaseModel):
    result: bool = Field(..., title="是否正确", description="纠错后的文本是否正确")
    reason: str = Field(..., title="原因", description="必须明确指出增加或者删除部分的内容")
# 判断纠错后的文本是否正确
@retry(stop=stop_after_attempt(3))
def judge_result(original_text, corrected_text):
    # parser = JsonOutputParser(pydantic_object=JudgeResult)
    parser = PydanticOutputParser(pydantic_object=JudgeResult)
    system_prompt = "你是一个优秀的文字编辑审核专家，判断编辑的修改是否正确。"
    human_prompt = f"""
判断纠错后的文本是否正确？
## 要求
1. 如果修改的原文和纠错后的文本完全一致，请回复“True”。
2. 如果修改后的文本更改了原文的意思，请回复“False”。
3. 如果修改后的文本还有其他错误，请回复“False”。
4. 输出的格式为{parser.get_format_instructions()}
## 例子
### 例子1
original_text：媒体和专家往往提倡大家奉行长期投资的理念，反对大家从事短期投机的活动，但是他们很难帮你区分哪一次买人是投机。
corrected_text：媒体和专家往往提倡大家奉行长期投资的理念，反对大家从事短期投机的活动，但是他们很难帮你区分哪一次买入是投机。
result：True
### 例子2
original_text：爱因斯坦说过这样一句话：  
Compound interest is the eighth wonder of the world.He who understands it,earns it..hewhodoesn't...paysit.  
（复利是“世界第八大奇迹”。知之者赚，不知之者被赚。）   
corrected_text:爱因斯坦说过这样一句话：  复利是“世界第八大奇迹”。知之者赚，不知之者被赚。  
result：False
reason: 删除了原文的内容 :“He who understands it,earns it..hewhodoesn't...paysit.”
### 例子3
original_text：那么，设计的最少必要知识是什么呢？其实，只要记住两个词就可以了：\n  简洁\n  # 留白  
corrected_text:根据上下文的内容，我们知道那么，设计的最少必要知识是什么呢？其实，只要记住两个词就可以了：\n  简洁\n  ## 留白  
result：False
reason 增加 "根据上下文的内容，我们知道那么，"内容
## 下面是内容
### <original_text>
{original_text}
### <corrected_text>
{corrected_text}

"""

    # ## 输出格式
    # {parser.get_format_instructions()}
    # parser_model = model.with_structured_output(JudgeResult)
    parser_model = model | parser
    out = parser_model.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(human_prompt)
            ]
        )
    if out is None:
        return JudgeResult(result=False, reason="")
    else:
        return out



# 首先读取md文件，然后分隔文本，调用模型，得到纠错后的文本，然后拼接回md文件

def run():
    file_path = r"C:\Users\jerri\work\pythonProject\ocr-pdf\财富自由之路\auto\财富自由之路.md"
    splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    with open(file_path, 'r', encoding='utf-8') as f:
        text = splitter.split_text(f.read())

    title_path = r"C:\Users\jerri\work\pythonProject\ocr-pdf\财富自由之路\auto\目录.txt"
    with open(title_path, 'r', encoding='utf-8') as f:
        title = f.read()
    title = title.split("#")
    right_text = []

    for i, t in enumerate(text):
        print(f"第{i+1}段")
        print("="*40)
        reason = ""
        print(f"第{i+1}段原文：{t}")
        out = make_right(title=title, input_text=t)
        print(f"第{i+1}段纠错后：{out}")
        result = judge_result(t, out)
        print(f"第{i+1}段纠错判断：{result.json()}")
        while not result.result:
            print(f"第{i+1}段纠错原因：{result.reason}")
            reason += result.reason + "\n"
            print(f"第{i+1}段原文：{t}")
            out = make_right(title=title, input_text=t, reason=reason)
            print(f"第{i+1}段再次纠错后：{out}")
            result = judge_result(t, out)
            print(f"第{i+1}段再次纠错判断：{result.json()}")
        right_text.append(out)

    # 写入纠错后的文本
    save_file_path = file_path.replace(".md", "_right.md")
    with open(save_file_path, 'w', encoding='utf-8') as f:
        for t in right_text:
            print(t)
            f.write(t)




if __name__ == '__main__':
    from langchain.globals import set_debug
    set_debug(True)
    title = """1.你知道自己的未来是什么样子的吗？001

2.你知道那条曲线究竟是什么吗？005

3.究竟什么是“财富自由”？012

4.起步时最重要的是什么？016"""
    t = """

# 2.你知道那条曲线究竟是什么吗？  

爱因斯坦说过这样一句话：  

Compound interest is the eighth wonder of the world.He who understands it,earns it..hewhodoesn't...paysit.  

（复利是“世界第八大奇迹”。知之者赚，不知之者被赚。）  """
    o = make_right(title, t)
    # print(o)
    # print(judge_result(t, o))
    run()

    # print(o)
    # run()
