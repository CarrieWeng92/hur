import psycopg2 
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    TemplateSendMessage, ImageCarouselTemplate, 
    ImageCarouselColumn, MessageTemplateAction, URITemplateAction,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, 
    TextComponent, CarouselContainer
)
from google import genai
from google.genai import types
app = Flask(__name__)
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

line_bot_api = LineBotApi(os.getenv("LINE_BOT_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_BOT_SECRET"))

ai_config = types.GenerateContentConfig(
    system_instruction="你是一個熱情、專業的台灣女團 HUR+ (Crimzon) 的粉絲小幫手，你的暱稱是『雷雷夥伴』。請用繁體中文回答粉絲的問題。如果粉絲問到成員資訊，請友善地介紹。回答要活潑一點，可以使用 Emoji。",
)

user_chat_mode = {}

DB_HOST = os.getenv("DB_HOST")      
DB_NAME = os.getenv("DB_NAME")  
DB_USER = os.getenv("DB_USER")  
DB_PASSWORD = os.getenv("DB_PASSWORD")    
DB_PORT = os.getenv("DB_PORT")      

# 放在 app.py 上面 import 的地方附近
def get_hur_data_prompt():
    try:
        # 連線資料庫 (記得要有 import psycopg2 和 os)
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cursor = conn.cursor()
        
        # 抓取所有成員的名字和擔當
        cursor.execute("SELECT name, intro FROM hur_members")
        rows = cursor.fetchall()
        
        # 把抓到的資料變成一段文字 (小抄)
        # 例如："成員：利善榛 (HUR+ 隊長...), 裴頡 (擔當...)"
        info_text = "HUR+ 的官方成員資料如下：\n"
        count = 0
        for row in rows:
            count += 1
            info_text += f"{count}. {row[0]}：{row[1]}\n"
            
        info_text += f"目前共有 {count} 位成員。\n請根據以上資料回答使用者的問題。"
        
        cursor.close()
        conn.close()
        return info_text
        
    except Exception as e:
        print("抓取成員資料失敗:", e)
        return "HUR+ 是一個台灣女團。" # 萬一資料庫壞掉的備用小抄

def save_log(user_id, message, sender):
    """
    sender: 輸入 'user' 或 'bot'
    """
    conn = None
    try:
        # 修改點 1: 使用 DATABASE_URL 連線
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cur = conn.cursor()
        
        # 修改點 2: 配合目前的資料表結構，不寫入 sender 欄位
        # 我們把 sender 加在訊息內容前面，例如 "[Bot] 訊息內容"
        log_message = f"[{sender}] {message}"
        
        sql = "INSERT INTO user_logs (user_id, message) VALUES (%s, %s)"
        cur.execute(sql, (user_id, log_message))
        conn.commit()
    except Exception as e:
        print(f"Log Error ({sender}): {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text
    user_id = event.source.user_id
    save_log(user_id, mtext, 'user')
    current_url = request.host_url.replace('http://', 'https://')
    baseurl = current_url + 'static/'

    if mtext == '@最新消息':
        try:
            message = TextSendMessage(
                text="💕最新消息!9 of 9 Fan Concert預計將在2026/1/24舉辦，請關注官方消息! "
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
         line_bot_api.reply_message(
             event.reply_token,
             TextSendMessage(text='發生錯誤!'))

    elif mtext == '@推薦歌曲':
        try:
            message = TextSendMessage(
                text="🎧 HUR+ 《GODDESS》Official Music Video:https://www.youtube.com/watch?v=dbasZ-WRbig"
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
             line_bot_api.reply_message(
                 event.reply_token, 
                 TextSendMessage(text='發生錯誤!'))

    elif mtext == '@成員專區':
        try:
            members = [
                {"label": "利善榛/個人單曲", "filename": "cindy.png",    "text": "我是利善榛，我的單曲大約在冬季已經上線了，點擊收聽\nhttps://www.kkbox.com/hk/tc/song/KoUXKmKBP2VFvwTjl-"},
                {"label": "裴頡/個人單曲",   "filename": "jasmine.png",  "text": "我是裴頡，我的單曲Baby Boy已經上線了，點擊收聽\nhttps://www.kkbox.com/tw/tc/song/5-S0W5Uei4L5rRgIx1"},
                {"label": "C.HOLLY/個人單曲","filename": "cholly.png",   "text": "我是C.HOLLY，我的單曲將在12/20上線，敬請期待"},
                {"label": "連穎/個人單曲",   "filename": "erin.png",     "text": "我是連穎，我的單曲將在1/03上線，可以先聽我的EP\nhttps://www.kkbox.com/tw/tc/album/T_gffhiL5SlJ-qtcKf"},
                {"label": "巴倫月/個人單曲", "filename": "sizi.png",     "text": "我是巴倫月，我的單曲Broken已經上線了，點擊收聽\nhttps://www.kkbox.com/tw/tc/song/8ofRcI4glULSDkgWjB"},
                {"label": "席子淇/個人單曲", "filename": "jennifer.png", "text": "我是席子淇，我的單曲909已經上線了，點擊收聽\nhttps://www.kkbox.com/tw/tc/song/D-49XwQmldMiklVMwi"},
                {"label": "佟凱玲/個人單曲", "filename": "shannon.png",  "text": "我是佟凱玲，我的單曲將在12/26上線，敬請期待"},
                {"label": "林詩雅/個人單曲", "filename": "grace.png",    "text": "我是林詩雅，我的單曲Refund已經上線了，點擊收聽\nhttps://www.kkbox.com/tw/tc/song/4r3n0YqASSJLr_s-yh"},
                {"label": "香蘭/個人單曲",   "filename": "lanlan.png",   "text": "我是香蘭，我的單曲可不可以別讓風吹亂我的心已經上線了，點擊收聽\nhttps://www.kkbox.com/hk/tc/album/OkdC5MgaH9M2vJXudF"}
            ]

            cols = []
            for member in members:
                img_url = baseurl + member['filename']
                if member['text'].startswith('http'):
                    action_obj = URITemplateAction(
                        label=member['label'][0:12],
                        uri=member['text']
                    )
                else:
                    action_obj = MessageTemplateAction(
                        label=member['label'][0:12],
                        text=member['text']
                    )

                col = ImageCarouselColumn(
                    image_url=img_url,
                    action=action_obj
                )
                cols.append(col)

            message = TemplateSendMessage(
                alt_text='HUR+ 成員介紹',
                template=ImageCarouselTemplate(columns=cols)
            )
            line_bot_api.reply_message(event.reply_token, message)

        except Exception as e:
            print(f"Error: {e}") 
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='圖片轉盤發生錯誤！'))

    elif mtext == '@成員資訊':
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
            )
            cur = conn.cursor()
            cur.execute("SELECT name, filename, intro FROM hur_members")
            rows = cur.fetchall()

            if not rows:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前資料庫中沒有成員資料喔！"))
                return

            # --- 製作 Flex Message 的泡泡 (Bubble) ---
            bubbles = []
            
            for row in rows:
                db_name = row[0]
                db_filename = row[1]
                db_intro = row[2]
                img_url = baseurl + db_filename

                # 建立單一成員的卡片 (Bubble)
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url=img_url,
                        size='full',
                        aspect_ratio='3:4', # 圖片比例，可改成 1:1 (正方形) 或 3:4 (直式)
                        aspect_mode='cover',
                        action=URITemplateAction(uri=img_url) # 點圖片可以放大看圖
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            # 1. 名字 (粗體大字)
                            TextComponent(text=db_name, weight='bold', size='xl', color='#1DB446'), # 綠色字體
                            # 2. 裝飾線
                            BoxComponent(
                                layout='vertical', margin='lg', spacing='sm',
                                contents=[
                                    BoxComponent(
                                        layout='baseline', spacing='sm',
                                        contents=[
                                            TextComponent(
                                                text='個人檔案',
                                                color='#aaaaaa',
                                                size='sm',
                                                flex=1
                                            ),
                                            TextComponent(
                                                text='Profile',
                                                color='#aaaaaa',
                                                size='sm',
                                                flex=5,
                                                align='end'
                                            )
                                        ]
                                    )
                                ]
                            ),
                            # 3. 介紹文字 (支援換行)
                            TextComponent(
                                text=db_intro,
                                wrap=True, # 自動換行
                                color='#666666',
                                size='sm',
                                margin='md'
                            )
                        ]
                    ),
                    # footer 可以放按鈕，這裡先留白，讓版面乾淨點
                )
                bubbles.append(bubble)

            # --- 將所有 Bubble 放入 Carousel (橫向捲動容器) ---
            flex_message = FlexSendMessage(
                alt_text='HUR+ 成員詳細檔案',
                contents=CarouselContainer(contents=bubbles)
            )

            line_bot_api.reply_message(event.reply_token, flex_message)

        except Exception as e:
            print(f"Flex Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'資料讀取失敗：{e}'))
        finally:
            if conn:
                cur.close()
                conn.close()

    elif mtext == '@互動機器人':
        user_chat_mode[user_id] = True
        
        msg = "⚡ 雷雷夥伴已上線！ ⚡\n\n現在你可以直接輸入文字跟我聊天囉！\n(想結束聊天請輸入「關閉」)"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        
    elif mtext == '關閉':
        user_chat_mode[user_id] = False
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚡ 雷雷夥伴已離線，我們下次見！\n(請點選下方選單使用其他功能)"))

    elif mtext.startswith("我是") and "單曲" in mtext:
         line_bot_api.reply_message(event.reply_token, TextSendMessage(text="收到！請雷雷們一起多多支持個人單曲喔！💜"))
         
    elif mtext == '@成員IG':
        try:
            message = TextSendMessage(
                text=(
            "追蹤HUR+官方IG:https://www.instagram.com/hur_official_/\n"
            "利善榛的IG：https://www.instagram.com/cindyli0318/\n"
            "裴頡的IG:https://www.instagram.com/jasminejadeperry/\n"
            "C.Holly的IG:https://www.instagram.com/c.holly.com_/\n"
            "連穎的IG：https://www.instagram.com/realerin6/\n"
            "巴倫月的IG:https://www.instagram.com/sizi_lunyue/\n"
            "席子淇的IG:https://www.instagram.com/jjjjner/\n"
            "佟凱玲IG:https://www.instagram.com/shannjacks/\n"
            "林詩雅的IG:https://www.instagram.com/gracelf/\n"
            "香蘭的IG：https://www.instagram.com/lan__0313/\n"
            )
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
             line_bot_api.reply_message(
                 event.reply_token, 
                 TextSendMessage(text='發生錯誤!'))
            
    else:
        if user_chat_mode.get(user_id) == True:
            try:
                # --- 修改部分開始：加入小抄邏輯 ---
                
                # 1. 呼叫函式取得資料庫裡正確的成員資料 (小抄)
                hur_data = get_hur_data_prompt()
                
                # 2. 組合提示詞：把小抄放在使用者的問題前面
                full_prompt = f"{hur_data}\n\n使用者問：{mtext}"
                
                # 3. 把組合好的 full_prompt 丟給 AI
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    config=ai_config,
                    contents=full_prompt 
                )
                result = response.text
                
                # 傳送給 Line
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
                
                # 2. 紀錄【AI】回的話 (sender='bot')
                save_log(user_id, result, 'bot')
                
            except Exception as e:
                print(f"AI Error: {e}")
                # ... (略)
        else:
            # 非聊天模式的提醒
            msg = "我不確定您的意思，請點選下方選單👇\n\n如果您想跟我聊天，請點選「互動機器人」按鈕喔！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            # 也可以紀錄機器人的這句提醒
            # save_log(user_id, msg, 'bot')

if __name__ == '__main__':

    app.run()


