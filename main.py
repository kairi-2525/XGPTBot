import tweepy
import time
import datetime
import openai
import random
import config

# クライアントの初期化
client = tweepy.Client(bearer_token=config.bearer_token, consumer_key=config.api_key, consumer_secret=config.api_secret_key, access_token=config.access_token, access_token_secret=config.access_token_secret)

# OpenAIのAPIキーを設定
openai_client = openai.OpenAI(api_key=config.openai_api_key)

# キャラクター設定
character_settings = {
    "name": "パスタ",
    "traits": "明るく元気で、少しおっとりしている。友達思いで誰とでもすぐに仲良くなれる。",
    "likes": "リプライをすること",
    "favorite_color": "ピンクと水色",
    "skills": "ゲーム、絵を描くこと、お菓子作り",
    "first_person": "ボク",
    "appearance": "ピンクと水色の髪、青い目、カジュアルな帽子とジャケット",
    "gender": "女性",
    "age": 16
}

# 通知時刻の設定
morning_hour = 6
night_hour = 22

def generate_greeting(hour):
    system_message = (
        f"あなたはキャラクター「パスタ」です。"
        f"{character_settings['name']}は{character_settings['traits']}な性格です。"
        f"好きなものは{character_settings['likes']}で、好きな色は{character_settings['favorite_color']}です。"
        f"特技は{character_settings['skills']}です。"
        f"外見は{character_settings['appearance']}。"
        f"{character_settings['age']}歳の{character_settings['gender']}で、一人称は「{character_settings['first_person']}」です。"
        f"指示されたメッセージをこのキャラクターになり切って前振り無しで発言する事"
    )
    
    prompt = f"今は{'朝' if hour == morning_hour else '夜'}なので、{character_settings['name']}らしい{'おはよう' if hour == morning_hour else 'おやすみ'}の挨拶日本語で"
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )
    
    message = response.choices[0].message.content.strip()
    return message

def ポストメッセージ(client, text):
    try:
        response = client.create_tweet(text=text)
        return f"ポストに成功しました！ {response}"
    except tweepy.TweepyException as e:
        return f"エラーが発生しました: {e}"

def 次の通知までの秒数を計算():
    now = datetime.datetime.now()
    random_minute = random.randint(0, 59)  # 0から59の間でランダムな分を生成
    next_morning = now.replace(hour=morning_hour, minute=random_minute, second=0, microsecond=0)
    next_night = now.replace(hour=night_hour, minute=random_minute, second=0, microsecond=0)
    
    if now < next_morning:
        next_notification = next_morning
    elif now < next_night:
        next_notification = next_night
    else:
        next_notification = next_morning + datetime.timedelta(days=1)

    print(f"次の通知時刻: {next_notification.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return (next_notification - now).total_seconds(), next_notification.hour

while True:
    sleep_seconds, next_hour = 次の通知までの秒数を計算()
    time.sleep(sleep_seconds)
    greeting_message = generate_greeting(next_hour)
    print(greeting_message)
    結果メッセージ = ポストメッセージ(client, greeting_message)
    print(結果メッセージ)
    time.sleep(60)  # 1分間待機して、連続通知を防ぐ