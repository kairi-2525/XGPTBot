import tweepy
import time
from datetime import datetime, timedelta
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
	"age": 16,
	"routine": "平日は学校に通っていてお菓子作りはできないけど、土日祝日にはお菓子を作ったり、友達と遊んだり、趣味のゲームをしたりしています。"
}

system_base_message = (
	f"あなたはキャラクター「{character_settings['name']}」"
	f"{character_settings['name']}は{character_settings['traits']}な性格"
	f"好きなものは{character_settings['likes']}で、好きな色は{character_settings['favorite_color']}"
	f"特技は{character_settings['skills']}です。"
	f"外見は{character_settings['appearance']}。"
	f"{character_settings['age']}歳の{character_settings['gender']}で、一人称は「{character_settings['first_person']}」"
	f"普段は、{character_settings['routine']}。"
	f"空白を含む全角140文字以内、半角なら280文字以内でツイートの文字数制限を超えないよう文章を生成する"
	f"このキャラクターになり切って指示された内容に合ったツイートの文章をハッシュタグ付きで生成する"
)

# 通知時刻の設定
morning_hour = 6
night_hour = 22
# 指定した時刻（時）の配列
specific_times = [
	{"hour": 6, "prompt": f"朝なので、{character_settings['name']}らしいおはようの挨拶を西暦は省略して日付と曜日、何の日かも知らせる形で日本語で"},
	{"hour": 15, "prompt": f"おやつの時間なので、{character_settings['name']}らしく今日の日付にちなんだおやつについて日本語で語って。"},
	{"hour": 22, "prompt": f"夜なので、{character_settings['name']}らしい就寝前のおやすみの挨拶を日本語で。何か出来事があれば軽く添えても良い"}
]

def generate_greeting(messages, prompt):
	additional_message = {"role": "user", "content": prompt}
	# 要素を追加
	messages.append(additional_message)
	response = openai_client.chat.completions.create(
		model="gpt-4o",
		messages=messages,
		max_tokens=150
	)

	message = response.choices[0].message.content.strip()
	messages.append({"role": "assistant", "content": message})
	return message

def post_message(client, text):
	try:
		response = client.create_tweet(text=text)
		return f"ポストに成功しました！ {response}"
	except tweepy.TweepyException as e:
		return f"エラーが発生しました: {e}"

# 配列に設定された時刻にランダムな分を付けて時刻配列にする
def prepare_times(day='today'):
	now = datetime.now()
	
	# 指定した日付に基づいて基準日を設定
	if day == 'tomorrow':
		base_day = now + timedelta(days=1)
	else:
		base_day = now

	system_message = system_base_message
	system_message += f"今日の日付は{base_day.strftime('%Y-%m-%d %H:%M')}、会話で使うときは基本西暦の年は省略する"
	messages=[
		{"role": "system", "content": system_message}
	]

	# 時刻とメッセージの配列をdatetimeオブジェクトに変換
	prepared_times = []
	for item in specific_times:
		hour = item["hour"]
		prompt = item["prompt"]
		target_time = datetime(base_day.year, base_day.month, base_day.day, hour, random.randint(0, 59), random.randint(0, 59))
		prepared_times.append({"time": target_time.strftime("%H:%M:%S"), "prompt": prompt})
		print(f"通知予定時刻: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")

	return prepared_times, messages

def print_at_times(messages, times):
	while times:
		# 現在時刻を取得
		now = datetime.now()

		# 時刻の配列をdatetimeオブジェクトに変換
		target_time = datetime.strptime(times[0]["time"], "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)

		wait_time = (target_time - now).total_seconds()
		if wait_time > 0:
			# ターゲット時刻まで待機
			print(f"次の通知時刻: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
			time.sleep(wait_time)
		else:
			times.pop(0)
			continue

		greeting_message = generate_greeting(messages, times[0]["prompt"])
		print(greeting_message)
		result_message = post_message(client, greeting_message)
		print(result_message)

		# 使用した時刻をリストから削除
		times.pop(0)

init_system_message = system_base_message
init_system_message += f"今日の日付と時刻は{datetime.now().strftime('%Y-%m-%d %H:%M')}、会話で使うときは基本西暦の年は省略する"
init_messages=[
	{"role": "system", "content": init_system_message}
]
for item in specific_times:
	greeting_message = generate_greeting(init_messages, item["prompt"])
	print(greeting_message)

times, messages = prepare_times('today')
print_at_times(messages, times)
while True:
	times, messages = prepare_times('tomorrow')
	print_at_times(messages, times)