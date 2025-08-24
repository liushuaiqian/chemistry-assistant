import base64
import os
from dashscope import MultiModalConversation


#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# 将xxxx/eagle.png替换为你本地图像的绝对路径
base64_image = encode_image("C:\\Users\\xiangteng\\Desktop\\test.png")

messages = [
    {"role": "system", "content": [{"text": "You are a helpful assistant."}]},
    {
        "role": "user",
        "content": [
            # 需要注意，传入Base64，图像格式（即image/{format}）需要与支持的图片列表中的Content Type保持一致。"f"是字符串格式化的方法。
            # PNG图像：  f"data:image/png;base64,{base64_image}"
            # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
            # WEBP图像： f"data:image/webp;base64,{base64_image}"
            {"image": f"data:image/png;base64,{base64_image}"},
            {"text": "图中描绘的是什么景象?"},
        ],
    },
]
response = MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key="sk-5a74911dfd884cc6abb87928f76f6994",
    model="qwen-vl-max-latest",  # 此处以qwen-vl-max-latest为例，可按需更换模型名称。模型列表：https://help.aliyun.com/model-studio/getting-started/model
    messages=messages,
)
print(response["output"]["choices"][0]["message"].content[0]["text"])