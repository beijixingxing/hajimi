<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini 常见问题及解决方法</title>
    <style>
        body {
            font-family: "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            margin: 20px;
            color: #333;
        }

        h1 {
            color: #2f5496;
            border-bottom: 2px solid #2f5496;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        h2 {
            color: #333;
            background-color: #f5f7fa;
            padding: 8px 12px;
            border-left: 5px solid #2f5496;
            margin-top: 30px;
            margin-bottom: 15px;
        }

        .question {
            font-weight: bold;
            color: #d9534f;
            margin-top: 15px;
            display: block;
        }

        .reason,
        .solution {
            margin: 8px 0;
            padding-left: 1em;
            text-indent: -1em;
        }

        .reason::before {
            content: "▶ 可能原因：";
            color: #666;
        }

        .solution::before {
            content: "🔧 解决办法：";
            color: #5cb85c;
        }
    </style>
</head>
<body>
    <h1>Gemini 常见问题及解决方法</h1>

    <!-- 网络与连接类 -->
    <h2>网络与连接类</h2>
    <span class="question">【internal server error】</span>
    <p class="reason">网络环境异常</p>
    <p class="solution">更换 VPN 节点，确保梯子开启全局 TUN 模式</p>

    <span class="question">【bad request】</span>
    <p class="reason">网络环境问题导致请求异常</p>
    <p class="solution">更换节点，梯子开启全局 TUN 模式</p>

    <!-- 请求与响应类 -->
    <h2>请求与响应类</h2>
    <span class="question">【API returned an error Unknown error occurred】或【API returned an error No candidates returned】</span>
    <p class="reason">非流式 AI 回复超酒馆 2min 响应上限被断开</p>
    <p class="solution">降低回复字数，或启用流式传输</p>

    <span class="question">【400 / Got response status 400】</span>
    <p class="reason">内容审核设置含无效参数值；Gemini随机出现（openrouter用户可调惩罚参数）</p>
    <p class="solution">openrouter用户，先调预设频率惩罚为0，不行再调存在惩罚为0</p>

    <span class="question">【400 / API returned an error Country, region, or territory not supported】</span>
    <p class="reason">梯子所处国家不支持Google AI Studio；梯子“不干净”</p>
    <p class="solution">切换对应节点，无效则换梯子</p>

    <span class="question">【403 / Forbidden】</span>
    <p class="reason">网络环境问题；账号/项目被封</p>
    <p class="solution">换梯子检查网络；核查账号/项目是否封禁</p>

    <span class="question">【403 / CONSUMER_SUSPENDED】</span>
    <p class="reason">项目已被封禁</p>
    <p class="solution">联系相关方处理封禁</p>

    <span class="question">【404 not found】</span>
    <p class="reason">模型选择错误</p>
    <p class="solution">重新选正确模型</p>

    <span class="question">【429】</span>
    <p class="reason">main prompt被标记</p>
    <p class="solution">换预设；把main prompt内容换语言、添加新内容</p>

    <span class="question">【429 / too many request】</span>
    <p class="reason">字面意思（也可能因429类原因）</p>
    <p class="solution">等待一会再重试</p>

    <span class="question">【429 / Gemini 2.5 Pro Preview doesn't have a free quota】</span>
    <p class="reason">2.5pro不支持免费使用</p>
    <p class="solution">充值付费</p>

    <span class="question">【500 server_error】</span>
    <p class="reason">上下文过长；Google服务器故障</p>
    <p class="solution">尝试切flash模式，仍报错则等待服务器恢复</p>

    <span class="question">【503 / SERVICE UNAVAILABLE / overload】</span>
    <p class="reason">服务不可用、服务器过载（或IP问题）</p>
    <p class="solution">只能等待，无其他解法</p>

    <span class="question">【Streaming request failed with status 504 Gateway Time-out】</span>
    <p class="reason">服务器响应超时</p>
    <p class="solution">开启流式传输测试；无效则为Google端问题，等待修复</p>

    <!-- 内容与预设类 -->
    <h2>内容与预设类</h2>
    <span class="question">【API returned an error Google AI Studio API returned no candidate Prompt was blocked due to:OTHER】</span>
    <p class="reason">内容被截断</p>
    <p class="solution">更换预设</p>

    <span class="question">【API returned an error Google AI Studio API returned no candidate Prompt was blocked due to:PROHIBITED_CONTENT】</span>
    <p class="reason">prompt违规，需求被拒</p>
    <p class="solution">换预设/开新对话；无效则联系卡作者排查卡问题</p>

    <span class="question">【Resource has been exhausted (e.g. check quota).】</span>
    <p class="reason">触发速率限制</p>
    <p class="solution">暂缓请求，等待限额重置</p>

    <span class="question">【中文回复中出现外语、八国联军】</span>
    <p class="reason">Gemini模型特性，外语回复污染上下文</p>
    <p class="solution">删除外语回复重新生成，出现即“重roll”</p>

    <span class="question">【空回复/截断】</span>
    <p class="reason">破限力度不足</p>
    <p class="solution">更换预设，加大预设破限强度</p>

    <span class="question">【No candidates returned：code 500】</span>
    <p class="reason">破限力度不足</p>
    <p class="solution">更换预设</p>

    <span class="question">【Google AI Studio Candidate text empty】</span>
    <p class="reason">输入截断</p>
    <p class="solution">在预设开启防输入截断条目，或换预设</p>

    <span class="question">【stream processing panic】</span>
    <p class="reason">——</p>
    <p class="solution">关闭流式，空回复时换预设</p>

    <!-- 特殊场景类 -->
    <h2>特殊场景类</h2>
    <span class="question">【User location is not supported for the API use.】</span>
    <p class="reason">IP被封禁</p>
    <p class="solution">换IP或用warp工具</p>

    <span class="question">【Unexpected error in chat_completions endpoint: Server disconnected without sending a response.】</span>
    <p class="reason">回复过慢，触发酒馆（平台）超时判定</p>
    <p class="solution">反代开假流；无效则强制开启流式传输</p>

</body>
</html>
