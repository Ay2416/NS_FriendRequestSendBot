# Discord bot import
import discord
from discord import app_commands
from discord import ui
import os
from dotenv import load_dotenv
#from time import sleep
from mk8dx import lounge_api
import glob
import ndjson
import time
import asyncio

# friendcode.py import
import base64
import datetime
import hashlib
import json
import random
import re
import requests
import secrets
import string
import sys
import uuid
import webbrowser

# Discordボットのプログラム部分
load_dotenv()
spreadsheet_apikey = "your_google_spreadsheet_api_key"

intents = discord.Intents.default()#適当に。
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

nintendo_client_id = "71b963c1b7b6d119" # Hardcoded in app, this is for the NSO app (parental control app has a different ID)
redirect_uri_regex = re.compile(r"npf71b963c1b7b6d119:\/\/auth#session_state=([0-9a-f]{64})&session_token_code=([A-Za-z0-9-._]+)&state=([A-Za-z]{50})")
rsess = requests.Session()

# bot start
@client.event
async def on_ready():
    print("接続しました！")
    await client.change_presence(activity=discord.Game(name="Ver.2.0 | /help"))
    await tree.sync()#スラッシュコマンドを同期
    print("グローバルコマンド同期完了！")
    
    # guild_ndjson, setup_json, user_json, language_jsonフォルダがあるかの確認
    files = glob.glob('./*')
    judge = 0
    
    for i in range(0, len(files)):
        #print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == "guild_ndjson"):
            print("guild_ndjsonファイルを確認しました！")
            judge = 1
            break

    if judge != 1:
        os.mkdir('guild_ndjson')
        print("guild_ndjsonファイルがなかったため作成しました！")

    judge = 0
    for i in range(0, len(files)):
        #print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == "setup_json"):
            print("setup_jsonファイルを確認しました！")
            judge = 1
            break

    if judge != 1:
        os.mkdir('setup_json')
        print("setup_jsonファイルがなかったため作成しました！！")

    judge = 0
    for i in range(0, len(files)):
        #print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == "user_json"):
            print("user_jsonファイルを確認しました！")
            judge = 1
            break

    if judge != 1:
        os.mkdir('user_json')
        print("user_jsonファイルがなかったため作成しました！！")
    
    judge = 0
    for i in range(0, len(files)):
        #print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == "language_json"):
            print("language_jsonファイルを確認しました！")
            judge = 1
            break

    if judge != 1:
        os.mkdir('language_json')
        print("language_jsonファイルがなかったため作成しました！！")

# サーバーに招待された場合に特定の処理をする
@client.event
async def on_guild_join(guild):
    file = str(guild.id) + ".json"

    content = {
        "language_mode" : "ja"
    }

    with open('./language_json/' + file, 'w') as f:
        json.dump(content, f, ensure_ascii=False)

# サーバーからキック、BANされた場合に特定の処理をする
@client.event
async def on_guild_remove(guild):
    file = str(guild.id) + ".json"
    os.remove("./language_json/" + file)

# /test
@tree.command(name="test",description="テストコマンドです。 / Test command.")
async def test_command(interaction: discord.Interaction,text:str):
    await interaction.response.defer(ephemeral=False)
    
    await interaction.followup.send("> " + text + "\n> " + text)

# /language
@tree.command(name="language",description="言語を変更します。（jaまたはen） / Change language. (ja or en)")
@discord.app_commands.choices(language=[discord.app_commands.Choice(name="ja",value="ja"),discord.app_commands.Choice(name="en",value="en")])
async def language_command(interaction: discord.Interaction,language:str):
    files = glob.glob('./language_json/*.json')
    judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.guild.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    file = str(interaction.guild.id) + ".json"

    if(judge == 1):
        os.remove("./language_json/" + file)

    content = {
        "language_mode" : language
    }

    with open('./language_json/' + file, 'w') as f:
        json.dump(content, f, ensure_ascii=False)

    if language == "ja":
        await interaction.response.send_message("日本語に変更しました。", ephemeral=False)
    elif language == "en":
        await interaction.response.send_message("Change English.", ephemeral=False)         

# /setup_step1
@tree.command(name="setup_step1",description="ニンテンドーアカウント認証用のリンクを作ります。/ Generate nintendo account login link.")
async def setup_step1(interaction: discord.Interaction):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    print("STEP 1: アカウント情報を取得するためブラウザを開きます")

    # def generate_challenge():
    verifier = secrets.token_bytes(32)
    verifier_b64 = base64.urlsafe_b64encode(verifier).decode().replace("=", "")

    s256 = hashlib.sha256()
    s256.update(verifier_b64.encode())

    challenge_b64 = base64.urlsafe_b64encode(s256.digest()).decode().replace("=", "")

    verifier = verifier_b64
    challenge = challenge_b64

    # def generate_state():
    # OAuth state is just a random opaque string
    alphabet = string.ascii_letters
    state = "".join(random.choice(alphabet) for _ in range(50))

    oauth_uri = "https://accounts.nintendo.com/connect/1.0.0/authorize?state={}&redirect_uri=npf71b963c1b7b6d119://auth&client_id=71b963c1b7b6d119&scope=openid%20user%20user.birthday%20user.mii%20user.screenName&response_type=session_token_code&session_token_code_challenge={}&session_token_code_challenge_method=S256&theme=login_form".format(state, challenge)

    content = {
        "verifier":{
            "verifier":verifier
        },
        "state":{
            "state":state
        }
    }

    with open('./setup_json/' + str(interaction.user.id) + ".json", 'w') as f:
        json.dump(content, f, ensure_ascii=False)
    
    if language == "ja":
        embed=discord.Embed(title="こちらでニンテンドーアカウントにログインしてください。", color=0xffffff)
        embed.add_field(name="・ログインしましたら、", value="　", inline=False)
        embed.add_field(name="パソコンの場合", value="「この人にする」ボタンを右クリックし「リンクアドレスをコピー」を選択して/setup_step2コマンドの[link_address]の部分でペーストしてください。", inline=False)
        embed.add_field(name="スマホの場合", value="「この人にする」ボタンを長押しして、「リンクアドレスをコピー」を選択して/setup_step2コマンドの[link_address]に部分でペーストしてください。", inline=False)
        embed.add_field(name="⇩URL⇩", value=oauth_uri, inline=False)
    elif language == "en":
        embed=discord.Embed(title="Please login to your Nintendo account here.", color=0xffffff)
        embed.add_field(name="・When I logged in,", value="　", inline=False)
        embed.add_field(name="For PC", value="Right click on the [Make this person] button, select [Copy link address] and paste it in the [link_address] section of the /setup_step2 command.", inline=False)
        embed.add_field(name="For phones,", value="Press and hold the [Make this person] button, select [Copy link address] and paste it in the [link_address] portion of the /setup_step2 command.", inline=False)
        embed.add_field(name="⇩URL⇩", value=oauth_uri, inline=False)
    await interaction.response.send_message(embed=embed,ephemeral=True)

# /setup_step2
@tree.command(name="setup_step2",description="/setup_step1のリンクアドレスを貼り付け、セットアップを開始します。 / /setup_step1 link paste, and start setup.")    
async def setup_step2(interaction: discord.Interaction, link_address:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./setup_json/*.json')
    judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        await interaction.response.defer(ephemeral=True)

        with open('./setup_json/' + str(interaction.user.id) + ".json") as f:
            jsn = json.load(f)

        
        verifier = jsn["verifier"]["verifier"]
        state = jsn["state"]["state"]
        oauth_redirect_uri = link_address

        # def parse_redirect_uri(uri):
        m = redirect_uri_regex.match(oauth_redirect_uri)
        redirect_uri_parsed = ""

        #print(m)

        if not m:
            redirect_uri_parsed = None
        else:
            redirect_uri_parsed = (m.group(1), m.group(2), m.group(3))

        #print(redirect_uri_parsed)
        #print(state)

        if not redirect_uri_parsed:
            print("Invalid redirect URI, aborting...")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:無効なリダイレクトURIです！:x:", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Invalid redirect URI, aborting...:x:", color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        session_state = redirect_uri_parsed[0]
        session_token_code = redirect_uri_parsed[1]
        response_state = redirect_uri_parsed[2]

        if state != response_state:
            print("Invalid redirect URI (bad OAuth state), aborting...")
            if language == "ja":
                embed=discord.Embed(title="Error!", description=":x:無効なリダイレクトURIです！（OAuthが原因）:x:", color=0xff0000)
            elif language == "en":    
                embed=discord.Embed(title="Error!", description=":x:Invalid redirect URI (bad OAuth state), aborting...:x:", color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        print("STEP 2: Nintendo APIにログイン中...")

        # def login_oauth_session(session_token_code, verifier):
        # Handles the second step of the OAuth process using the information we got from the redirect API
        resp = rsess.post("https://accounts.nintendo.com/connect/1.0.0/api/session_token", data={
            "client_id": nintendo_client_id,
            "session_token_code": session_token_code,
            "session_token_code_verifier": verifier
        }, headers={
            "User-Agent": "OnlineLounge/2.5.1 NASDKAPI Android"
        })
        if resp.status_code != 200:
            print("Error obtaining session token from Nintendo, aborting... ({})".format(resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:任天堂からのセッショントークンの取得に失敗しました。 ({}):x:".format(resp.text), color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Error obtaining session token from Nintendo, aborting... ({}):x:".format(resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        response_data = resp.json()
        session_token = response_data["session_token"]

        # def login_nintendo_api(session_token):
        # This properly "logs in" to the Nintendo API getting us a token we can actually use for something practical
        resp = rsess.post("https://accounts.nintendo.com/connect/1.0.0/api/token", data={
            "client_id": nintendo_client_id,
            "session_token": session_token,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token"
        }, headers={
            "User-Agent": "OnlineLounge/2.5.1 NASDKAPI Android"
        })
        if resp.status_code != 200:
            print("Error obtaining service token from Nintendo, aborting... ({})".format(resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:任天堂からサービストークンを取得する際にエラーが発生しました。 ({}):x:".format(resp.text), color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Error obtaining service token from Nintendo, aborting... ({}):x:".format(resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        response_data = resp.json()

        id_token = response_data["id_token"]
        access_token = response_data["access_token"]

        print("STEP 3: Switch APIにログイン中...")

        # def get_nintendo_account_data(access_token):
        # This fetches information about the currently logged-in user, including locale, country and birthday (needed later)
        resp = rsess.get("https://api.accounts.nintendo.com/2.0.0/users/me", headers={
            "User-Agent": "OnlineLounge/2.5.1 NASDKAPI Android",
            "Authorization": "Bearer {}".format(access_token)
        })
        if resp.status_code != 200:
            print("Error obtaining account data from Nintendo, aborting... ({})".format(resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:任天堂からアカウントデータを取得する際にエラーが発生しました。 ({}):x:".format(resp.text), color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Error obtaining account data from Nintendo, aborting... ({}):x:".format(resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        nintendo_account_data = resp.json()

        #print(" > Nintendo account data: {}".format(nintendo_account_data))

        # def login_switch_web(id_token, nintendo_profile):
        # This logs into the Switch-specific API using a bit of a mess of third-party APIs to get the codes sorted
        timestamp = str(int(datetime.datetime.utcnow().timestamp()))
        request_id = str(uuid.uuid4())
        #request_id2 = str(uuid.uuid4())

        print("> Eli Fessler's S2S APIでハッシュを計算中...")

        # def call_s2s(token, timestamp):
        # I'm not entirely sure what this API does but it gets you a code that you need to move on.

        token = id_token

        resp = rsess.post("https://elifessler.com/s2s/api/gen2", data={
            "naIdToken": token,
            "timestamp": timestamp
        }, headers={
            "User-Agent": "testapp/@AT12806379" # This is just me testing things, replace this with a real user agent in a real-world app
        })
        if resp.status_code != 200:
            print("Error obtaining auth hash from Eli Fessler's S2S server, aborting... ({})".format(resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:Eli FesslerのS2Sサーバーから認証ハッシュを取得する際にエラーが発生しました。 ({}):x:".format(resp.text), color=0xff0000)           
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Error obtaining auth hash from Eli Fessler's S2S server, aborting... ({}):x:".format(resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)
        nso_hash = resp.json()["hash"]

        print("> f-code を imink APIで計算中...")

        # def call_flapg(id_token, timestamp, request_id, hash, type):
        # Calls the flapg API to get an "f-code" for a login request
        # this is generated by the NSO app but hasn't been reverse-engineered at the moment.
        type = "nso"

        flapg_resp = rsess.post("https://api.imink.app/f", json={
            # "User-Agent": "testapp/@AT12806379",
            # "Content-Type": "application/json; charset=utf-8",
            "token": id_token,
            "hash_method": "1",
            "timestamp": timestamp,
            "request_id": request_id
        })
        #print(flapg_resp.json)
        if flapg_resp.status_code != 200:
            print("Error obtaining f-code from imink API, aborting... ({})".format(flapg_resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description="imink APIからf-codeを取得する際にエラーが発生しました。 ({})".format(flapg_resp.text), color=0xff0000)           
            elif language == "en":
                embed=discord.Embed(title="Error!", description="Error obtaining f-code from imink API, aborting... ({})".format(flapg_resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return

        nso_f = flapg_resp.json()["f"]
        registrationToken = flapg_resp.json()["request_id"]

        print("> Nintendo Switch APIにログイン中...")

        nintendo_profile = nintendo_account_data

        resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v1/Account/Login", json={
            "parameter": {
                "f": nso_f,
                "naIdToken": id_token,
                "timestamp": timestamp,
                "requestId": request_id,
                "naBirthday": nintendo_profile["birthday"],
                "naCountry": nintendo_profile["country"],
                "language": nintendo_profile["language"]
            }
        }, headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
            "X-ProductVersion": "2.5.1",
            "X-Platform": "Android"
        })

        if resp.status_code != 200 or "errorMessage" in resp.json():
            print("Error logging into Switch API, aborting... ({})".format(resp.text))
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:Switch APIへのログインでエラーが発生しました。 ({}):x:".format(resp.text), color=0xff0000)            
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Error logging into Switch API, aborting... ({}):x:".format(resp.text), color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        web_token = resp.json()["result"]["webApiServerCredential"]["accessToken"]

        content = {
            "web_token":{
                "web_token":web_token
            },
            "time":{
                "time":time.time()
            }
        }

        with open('./user_json/' + str(interaction.user.id) + ".json", 'w') as f:
            json.dump(content, f, ensure_ascii=False)
        #print(" > Switch web token: {}".format(switch_web_token))

        print("準備完了!")
        os.remove("./setup_json/" + str(interaction.user.id) + ".json")
        if language == "ja":
            embed=discord.Embed(title="成功しました!", description="認証成功！\n2時間後に認証が切れてしまいますのでそれ以上使う場合はもう1度/setup_step1,/setup_step2コマンドを実行してください。", color=0x00ff40)
        elif language == "en":
            embed=discord.Embed(title="Success!", description="Authentication succeeded!\nThe authentication will expire after 2 hours, so please execute the /setup_step1,/setup_step2 command once more if you want to use it longer.", color=0x00ff40)
        await interaction.followup.send(embed=embed)
    else:
        print("Error!:最初に/setup_step1コマンドでセットアップを行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="最初に/setup_step1コマンドでセットアップを行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="First, please use the /setup_step1 command to set up the system.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /finish
@tree.command(name="finish",description="フレンド申請のプログラムを終了させます。 / Finish friend request program.")
async def finish(interaction: discord.Interaction):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./user_json/*.json')
    judge = 0

    for i in range(0, len(files)):
        #print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        os.remove("./user_json/" + str(interaction.user.id) + ".json")

        print("User data deleted.")
        if language == "ja":
            embed=discord.Embed(title="終了処理が完了しました！", description="また使う際は、/setup_step1,/setup_step2コマンドを行ってからご使用ください！", color=0x00ff40)
        elif language == "en":
            embed=discord.Embed(title="The termination process has been completed!", description="When using it again, please do the /setup_step1 and /setup_step2 commands before use!", color=0x00ff40)           
        await interaction.response.send_message(embed=embed)
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="First, please use the /setup_step1, /setup_step2 command to set up the system.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /help
@tree.command(name="help",description="コマンドについての簡単な使い方を出します。 / Command details.")
async def help(interaction: discord.Interaction):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    if language == "ja":
        embed=discord.Embed(title="コマンドリスト")
        embed.add_field(name="/setup_step1", value="このBotを使うに当たってセットアップに必要な任天堂アカウントログイン用のURLを発行します。", inline=False)
        embed.add_field(name="/setup_step2 [/setup_step1でコピーをしたURL]", value="このBotを使うに当たってセットアップに必要なセットアップを完了させます。", inline=False)
        embed.add_field(name="/finish", value="このBotでの処理を終了し、セットアップが必要な初期状態に戻します。\n（※使い終わったら必ず実行してください。次回以降の使用に影響が出る可能性があります。）", inline=False)
        embed.add_field(name="/help", value="このBotのコマンドの簡単な使い方を出します。", inline=False)
        embed.add_field(name="/language [ja/en]", value="言語を変更します。", inline=False)
        embed.add_field(name="/server_num", value="このBotの導入されているサーバー数を表示します。", inline=False)
        embed.add_field(name="/fr [SWを除くフレンドコード（例：1234-5678-9012）]", value="セットアップしたアカウントから指定のフレンドコードに対して、フレンド申請を行います。「,」で区切ることで複数人に対してフレンド申請を送ることが可能です。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="/lounge_fr [MK8DXラウンジ名]", value="セットアップしたアカウントから入力されたMK8DXラウンジ名の人に対して、フレンド申請を行います。「,」で区切ることで複数人に対してフレンド申請を送ることが可能です。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="/spreadsheet_fr [共有リンク] [シート名] [範囲（Excelの「○○:○○」の指定方法に準ずる）]", value="セットアップしたアカウントからスプレッドシートの指定された範囲のフレンドコードに対してフレンド申請を行います。\nフレンドコードはSWを除く形（例：1234-5678-9012）で書いてください。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="/sstemplate_set [登録したいテンプレート名] [共有リンク] [シート名] [範囲（Excelの「○○:○○」の指定方法に準ずる）]", value="/sstemplate_frを実行するためのテンプレートの登録を行います。", inline=False)
        embed.add_field(name="/sstemplate_list", value="/sstemplate_frを実行するためのテンプレートの一覧を表示します。", inline=False)
        embed.add_field(name="/sstemplate_delete [登録したテンプレート名]", value="/sstemplate_frを実行するためのテンプレートの削除を行います。", inline=False)
        embed.add_field(name="/sstemplate_fr [登録したテンプレート名]", value="セットアップしたアカウントからテンプレート登録したスプレッドシートの指定された範囲のフレンドコードに対してフレンド申請を行います。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="※こちらから詳しい使い方を確認してください!↓", value="https://ay2416.github.io/NSO-FriendRequestSendBot/", inline=False)
    elif language == "en":
        embed=discord.Embed(title="Command list")
        embed.add_field(name="/setup_step1", value="The URL for the Nintendo account login required for setup when using this bot will be issued.", inline=False)
        embed.add_field(name="/setup_step2 [URL copied in /setup_step1]", value="Complete the setup required to use this bot.", inline=False)
        embed.add_field(name="/finish", value="Terminates the process with this bot and returns it to the initial state where setup is required.\n(*Be sure to execute this after you have finished using the bot. It may affect the next and subsequent uses.)", inline=False)
        embed.add_field(name="/help", value="I will give a brief usage of this bot's commands.", inline=False)
        embed.add_field(name="/language [ja/en]", value="Change language.", inline=False)
        embed.add_field(name="/server_num", value="Displays the number of servers where this bot is installed.", inline=False)
        embed.add_field(name="/fr [Friend code excluding SW (e.g., 1234-5678-9012)]", value="A friend request will be sent to the specified friend code from the set up account. You can send a friend request to multiple people by separating them with [,].\n(* Available after completing /setup_step1 and /setup_step2)", inline=False)
        embed.add_field(name="/lounge_fr [MK8DX Lounge name]", value="A friend request will be sent from your setup account to the person with the MK8DX lounge name entered. You can send a friend request to multiple people by separating them with [,].\n(* Available after completing /setup_step1 and /setup_step2)", inline=False)
        embed.add_field(name="/spreadsheet_fr [Share link] [sheet name(e.g., sheet1)] [Range (similar to how XX:XX is specified in Excel)]", value="Make a friend request from the set up account to the friend code in the range specified in the spreadsheet. Please write the \n friend code in the form excluding SW (e.g. 1234-5678-9012).\n(*Available after completing /setup_step1,/setup_step2)", inline=False)
        embed.add_field(name="/sstemplate_set [Name of template you want to register] [Share link] [sheet name(e.g., sheet1)] [Range (similar to how XX:XX is specified in Excel)]", value="Register a template to run /sstemplate_fr.", inline=False)
        embed.add_field(name="/sstemplate_list", value="List of templates to run /sstemplate_fr.", inline=False)
        embed.add_field(name="/sstemplate_delete [Registered template name]", value="Delete templates to run /sstemplate_fr.", inline=False)
        embed.add_field(name="/sstemplate_fr [Registered template name]", value="Friend request from the setup account to the specified range of friend codes in the template-registered spreadsheet.\n(*available after completing /setup_step1 and /setup_step2)", inline=False)
        #embed.add_field(name="※こちらから詳しい使い方を確認してください!↓", value="https://ay2416.github.io/NSO-FriendRequestSendBot/", inline=False)
    await interaction.response.send_message(embed=embed,ephemeral=False)

# /server_num
@tree.command(name="server_num",description="導入されているサーバー数を取得します。 / View server num.")
async def server_num(interaction: discord.Interaction):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    if language == "ja":
        embed=discord.Embed(title="導入サーバー数", description=str(len(client.guilds)) + " サーバー")
    elif language == "en":
        embed=discord.Embed(title="Number of servers installed", description=str(len(client.guilds)) + " server")
    
    await interaction.response.send_message(embed=embed)

# /fr
@tree.command(name="fr",description="フレンドコードからフレンド申請を行います。 / Friend code friend request.")
async def fr_command(interaction: discord.Interaction,code:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./user_json/*.json')
    judge = 0
    response_num = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        player_fc = code.split(',')

        with open('./user_json/' + str(interaction.user.id) + ".json") as f:
            jsn = json.load(f)
        
        if time.time() - jsn["time"]["time"] >= 7200:
                print("Error!:前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。")
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description="It has been two hours since the last authentication.\nPlease execute the /setup_step1 and /setup_step2 commands to authenticate again.", color=0xff0000)
                   
                os.remove("./user_json/" + str(interaction.user.id) + ".json")
                await interaction.response.send_message(embed=embed,ephemeral=False)
                return
        
        await interaction.response.defer()

        web_token = jsn["web_token"]["web_token"]

        allmessage = ""
        message = ""
        for i in range(0, len(player_fc)):
            # def search_friend_code(web_token):
            friend_code = player_fc[i]
            message = "**" + str(i+1) + ". " + friend_code + "**"
            if(response_num == 0):
                allmessage = allmessage + message + "\n"
                await interaction.followup.send(allmessage)
                response_num = 1
            else:
                allmessage = allmessage + "\n"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)

            if re.match('[\d]{4}-[\d]{4}-[\d]{4}$', friend_code):
                resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/Friend/GetUserByFriendCode", json={
                    "parameter": {
                        "friendCode": friend_code
                    }
                }, headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error searching for friend code, aborting... ({})".format(resp.text))
                    if language == "ja":
                        message = "> エラー! :x:フレンドコードの検索でエラーが発生しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                    elif language == "en":
                        message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
                    #sys.exit(1)
                print("{}さんにフレンド申請します".format(resp.json()["result"]["name"]))
                friend_name = resp.json()["result"]["name"]
                nsaId = resp.json()["result"]["nsaId"]

                nsa_id = nsaId

                resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/FriendRequest/Create", json={
                    "parameter": {
                        "nsaId": nsa_id
                    }
                }, headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error sending friend request, aborting... ({})".format(resp.text))
                    if language == "ja":
                        message = "> エラー! :x:フレンドリクエストの送信に失敗しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                    elif language == "en":
                        message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
                    #sys.exit(1)
                print("フレンド申請を送信しました")
                if language == "ja":
                    message = "> " + friend_name + "さんにフレンド申請しました！"
                elif language == "en":
                    message = "> Friend request has been sent to" + friend_name + "!"  
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                await asyncio.sleep(10)
            else:
                print("Error!:Not friend code! your typing code:" + friend_code)
                if language == "ja":
                    message = "> Error! :x:フレンドコードではありません!:x: ```該当するフレンドコード:" + friend_code + "\n```"
                elif language == "en":    
                    message = "> Error! :x:Not friend code!:x: ```your typing code:" + friend_code + "\n```"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                await asyncio.sleep(10)
                continue

        print("Success!:全ての処理が終わりました！")
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="First, please use the /setup_step1, /setup_step2 command to set up the system.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /lounge_fr
@tree.command(name="lounge_fr",description="MK8DXラウンジの名前からフレンド申請を行います。 / Lounge name friend request.")
async def lounge_fr_command(interaction: discord.Interaction,lounge_name:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./user_json/*.json')
    judge = 0
    response_num = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        name_data = lounge_name.split(',')

        with open('./user_json/' + str(interaction.user.id) + ".json") as f:
            jsn = json.load(f)

        if time.time() - jsn["time"]["time"] >= 7200:
                print("Error!:前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。")
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description="It has been two hours since the last authentication.\nPlease execute the /setup_step1 and /setup_step2 commands to authenticate again.", color=0xff0000)
                   
                os.remove("./user_json/" + str(interaction.user.id) + ".json")
                await interaction.response.send_message(embed=embed,ephemeral=False)
                return

        await interaction.response.defer()

        web_token = jsn["web_token"]["web_token"]

        player_fc = []
        
        for i in range(0, len(name_data)):
            player = await lounge_api.get_player(name=name_data[i])
            print(player)

            if player == None:
                print("Error!: Lounge name Not found.")
                player_fc.append('0')
            else:
                player_fc.append(player.switch_fc)
        
        #print(player_fc)
        
        allmessage = ""
        message = ""
        for i in range(0, len(player_fc)):

            # def search_friend_code(web_token):
            friend_code = player_fc[i]
            
            message = "**" + str(i+1) + ". " + name_data[i] + "**"
            if(response_num == 0):
                allmessage = allmessage + message + "\n"
                await interaction.followup.send(allmessage)
                response_num = 1
            else:
                allmessage = allmessage + "\n"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)

            if re.match('[\d]{4}-[\d]{4}-[\d]{4}$', friend_code):
                resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/Friend/GetUserByFriendCode", json={
                    "parameter": {
                        "friendCode": friend_code
                    }
                }, headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error searching for friend code, aborting... ({})".format(resp.text))
                    if language == "ja":
                        message = "> エラー! :x:フレンドコードの検索でエラーが発生しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                    elif language == "en":
                        message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
                    #sys.exit(1)
                print("{}さんにフレンド申請します".format(resp.json()["result"]["name"]))
                friend_name = resp.json()["result"]["name"]
                #print(friend_name)
                nsaId = resp.json()["result"]["nsaId"]

                nsa_id = nsaId

                resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/FriendRequest/Create", json={
                    "parameter": {
                        "nsaId": nsa_id
                    }
                }, headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error sending friend request, aborting... ({})".format(resp.text))
                    if language == "ja":
                        message = "> エラー! :x:フレンドリクエストの送信に失敗しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                    elif language == "en":
                        message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
                    #sys.exit(1)
                print("フレンド申請を送信しました")
                if language == "ja":
                    message = "> " + friend_name + "さんにフレンド申請しました！"
                elif language == "en":
                    message = "> Friend request has been sent to" + friend_name + "!"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                await asyncio.sleep(10)
            else:
                print("Error!:Not friend code! your typing lounge name Not found!:" + name_data[i])
                if language == "ja":
                    message = "> Error! :x:フレンドコードではありません!:x: ```該当するフレンドコード:" + friend_code + "\n```"
                elif language == "en":    
                    message = "> Error! :x:Not friend code!:x: ```your typing code:" + friend_code + "\n```"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                await asyncio.sleep(10)
                continue
        
        print("Success!:全ての処理が終わりました！")
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="First, please use the /setup_step1, /setup_step2 command to set up the system.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)
        #await interaction.response.send_message("test message",ephemeral=False)

# /spreadsheet_fr
@tree.command(name="spreadsheet_fr",description="スプレッドシートの指定の範囲にあるフレンドコードに対してフレンド申請を行います。 / Spreadsheet friend request.")
async def spreadsheet_fr_command(interaction: discord.Interaction,spreadsheet_url:str,sheet_name:str,selected_range:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./user_json/*.json')
    judge = 0
    response_num = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        with open('./user_json/' + str(interaction.user.id) + ".json") as f:
            jsn = json.load(f)
        
        if time.time() - jsn["time"]["time"] >= 7200:
            print("Error!:前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description="It has been two hours since the last authentication.\nPlease execute the /setup_step1 and /setup_step2 commands to authenticate again.", color=0xff0000)

            os.remove("./user_json/" + str(interaction.user.id) + ".json")
            await interaction.response.send_message(embed=embed,ephemeral=False)
            return

        web_token = jsn["web_token"]["web_token"]
        allmessage = ""
        message = ""
        
        if spreadsheet_url[0:37] == 'https://docs.google.com/spreadsheets/':
            # debug message start
            print('-Change start-')
            print('')

            print(spreadsheet_url)
            print('')

            url = spreadsheet_url[39:]
            print(url)
            print('')

            id = url.split('/')[0]
            print(id)
            print('')

            print('-Change finish!-')
            print('')
        else:
            # debug message start
            print('-Change start!-')
            print('')

            print('Error!:Not Support Link or No Link!')
            print('')

            print('-Change finish!-')
            print('')
            # debug message finish

            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:このリンクはサポートされていないか、リンクではありません！:x:", color=0xff0000)
            elif language == "en":    
                embed=discord.Embed(title="Error!", description=":x:Not Support Link or No Link!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)
        
        if re.match('[\w][\d]:[\w][\d]', selected_range) or re.match('[\w][\d][\d]:[\w][\d][\d]', selected_range):
            await interaction.response.defer()

            url = requests.get("https://sheets.googleapis.com/v4/spreadsheets/" + id + "/values/" + sheet_name + "!" + selected_range + "?key=+" + spreadsheet_apikey)
            text = url.text

            data = json.loads(text)

            #codedata = data["values"]
            print(data["values"])

            codedata = []
            for i in range(0, len(data["values"])):
                codedata.append(data["values"][i][0])
            
            print(codedata)
            # num = len(codedata)
            # print(num)
            # print(codedata[0][0])

            for i in range(0, len(codedata)):
                # def search_friend_code(web_token):
                friend_code = codedata[i]
                
                message = "**" + str(i+1) + ". " + friend_code + "**"
                if(response_num == 0):
                    allmessage = allmessage + message + "\n"
                    await interaction.followup.send(allmessage)
                    response_num = 1
                else:
                    allmessage = allmessage + "\n"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)

                if re.match('[\d]{4}-[\d]{4}-[\d]{4}$', friend_code):

                    resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/Friend/GetUserByFriendCode", json={
                        "parameter": {
                            "friendCode": friend_code
                        }
                    }, headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error searching for friend code, aborting... ({})".format(resp.text))
                        if language == "ja":
                            message = "> エラー! :x:フレンドコードの検索でエラーが発生しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                        elif language == "en":
                            message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                        continue
                        #sys.exit(1)
                    print("{}さんにフレンド申請します".format(resp.json()["result"]["name"]))
                    friend_name = resp.json()["result"]["name"]

                    nsaId = resp.json()["result"]["nsaId"]

                    nsa_id = nsaId

                    resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/FriendRequest/Create", json={
                        "parameter": {
                            "nsaId": nsa_id
                        }
                    }, headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error sending friend request, aborting... ({})".format(resp.text))
                        if language == "ja":
                            message = "> エラー! :x:フレンドリクエストの送信に失敗しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                        elif language == "en":
                            message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                        continue
                        #sys.exit(1)
                    print("フレンド申請を送信しました")
                    if language == "ja":
                        message = "> " + friend_name + "さんにフレンド申請しました！"
                    elif language == "en":
                        message = "> Friend request has been sent to" + friend_name + "!"  
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                else:
                    print("Error!:Not friend code! friend code:" + friend_code)
                    if language == "ja":
                        message = "> Error! :x:フレンドコードではありません!:x: ```該当するフレンドコード:" + friend_code + "```"
                    elif language == "en":    
                        message = "> Error! :x:Not friend code!:x: ```your typing code:" + friend_code + "```"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
        else:
            print("Error!:Not support range!")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:この範囲指定はサポートしていません！:x:", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Not support range!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)

        print("Success!:全ての処理が終わりました！")

    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="First, please use the /setup_step1, /setup_step2 command to set up the system.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

    files = glob.glob('./user_json/*.json')
    judge = 0
    response_num = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        with open('./user_json/' + str(interaction.user.id) + ".json") as f:
            jsn = json.load(f)
        
        if time.time() - jsn["time"]["time"] >= 7200:
            print("Error!:前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。")
            embed=discord.Embed(title="エラー!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
            os.remove("./user_json/" + str(interaction.user.id) + ".json")
            await interaction.response.send_message(embed=embed,ephemeral=False)
            return

        web_token = jsn["web_token"]["web_token"]
        allmessage = ""
        message = ""
        
        if spreadsheet_url[0:37] == 'https://docs.google.com/spreadsheets/':
            # debug message start
            print('-Change start-')
            print('')

            print(spreadsheet_url)
            print('')

            url = spreadsheet_url[39:]
            print(url)
            print('')

            id = url.split('/')[0]
            print(id)
            print('')

            print('-Change finish!-')
            print('')
        else:
            # debug message start
            print('-Change start!-')
            print('')

            print('Error!:Not Support Link or No Link!')
            print('')

            print('-Change finish!-')
            print('')
            # debug message finish

            embed=discord.Embed(title="エラー!", description=":x:このリンクはサポートされていないか、リンクではありません！:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)
        
        if re.match('[\w][\d]:[\w][\d]', selected_range) or re.match('[\w][\d][\d]:[\w][\d][\d]', selected_range):
            await interaction.response.defer()

            url = requests.get("https://sheets.googleapis.com/v4/spreadsheets/1myKshELYBcxFjydTSRzWK7qjuXHddQcU9SAbQ2TkXY0/values/シート1!J6:J17?key=" + spreadsheet_apikey)
            text = url.text

            data = json.loads(text)

            #codedata = data["values"]
            print(data["values"])

            codedata = []
            for i in range(0, len(data["values"])):
                codedata.append(data["values"][i][0])
            
            print(codedata)
            # num = len(codedata)
            # print(num)
            # print(codedata[0][0])

            for i in range(0, len(codedata)):
                # def search_friend_code(web_token):
                friend_code = codedata[i]

                message = "**" + str(i+1) + ". " + friend_code + "**"
                if(response_num == 0):
                    allmessage = allmessage + message + "\n"
                    await interaction.followup.send(allmessage)
                    response_num = 1
                else:
                    allmessage = allmessage + "\n"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)

                if re.match('[\d]{4}-[\d]{4}-[\d]{4}$', friend_code):

                    resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/Friend/GetUserByFriendCode", json={
                        "parameter": {
                            "friendCode": friend_code
                        }
                    }, headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error searching for friend code, aborting... ({})".format(resp.text))
                        message = "> エラー! :x:フレンドコードの検索でエラーが発生しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                        continue
                        #sys.exit(1)
                    print("{}さんにフレンド申請します".format(resp.json()["result"]["name"]))
                    friend_name = resp.json()["result"]["name"]

                    nsaId = resp.json()["result"]["nsaId"]

                    nsa_id = nsaId

                    resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/FriendRequest/Create", json={
                        "parameter": {
                            "nsaId": nsa_id
                        }
                    }, headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error sending friend request, aborting... ({})".format(resp.text))
                        message = "> エラー! :x:フレンドリクエストの送信に失敗しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                        continue
                        #sys.exit(1)
                    print("フレンド申請を送信しました")
                    message = "> " + friend_name + "さんにフレンド申請しました！"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                else:
                    print("Error!:Error! :x:Not friend code! friend code:" + friend_code)
                    message = "> Error! :x:フレンドコードではありません!:x: ```該当するフレンドコード:" + friend_code + "```"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    await asyncio.sleep(10)
                    continue
        else:
            print("Error!:Not support Range!")
            embed=discord.Embed(title="エラー!", description=":x:この範囲指定はサポートしていません！:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)

        print("Success!:全ての処理が終わりました！")
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /sstemplate_set
@tree.command(name="sstemplate_set",description="/sstemplate_frで実行するためのテンプレートを作成します。 / Create  to use [/sstemplate_fr] command template.")
async def sstemplate_set_command(interaction: discord.Interaction,template_name:str,spreadsheet_url:str,sheet_name:str,selected_range:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./guild_ndjson/*.ndjson')
    judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.guild.id) + ".ndjson"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        file = str(interaction.guild.id) + ".ndjson"
        with open('./guild_ndjson/' + file) as f:
                    read_data = ndjson.load(f)
        
        for i in range(0, len(read_data)):
            if template_name == read_data[i]["template_name"]:
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description=":x:既に同じ名前のテンプレートがあります。:x:", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description=":x:There is already a template with the same name.:x:", color=0xff0000)                    
                await interaction.response.send_message(embed=embed)

        if spreadsheet_url[0:37] == 'https://docs.google.com/spreadsheets/':
            # debug message start
            print('-Change start-')
            print('')

            print(spreadsheet_url)
            print('')

            url = spreadsheet_url[39:]
            print(url)
            print('')

            id = url.split('/')[0]
            print(id)
            print('')

            print('-Change finish!-')
            print('')
        else:
            # debug message start
            print('-Change start!-')
            print('')

            print('Error!:Not Support Link or No Link!')
            print('')

            print('-Change finish!-')
            print('')
            # debug message finish

            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:このリンクはサポートされていないか、リンクではありません！:x:", color=0xff0000)
            elif language == "en":    
                embed=discord.Embed(title="Error!", description=":x:Not Support Link or No Link!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)
        
        if re.match('[\w][\d]:[\w][\d]', selected_range) or re.match('[\w][\d][\d]:[\w][\d][\d]', selected_range):
            await interaction.response.defer()
            content = {
                "template_name" : template_name,
                "spreadsheet_id": id,
                "sheet_name": sheet_name,
                "selected_range" : selected_range
            }

            file = str(interaction.guild.id) + ".ndjson"
            with open('./guild_ndjson/' + file, 'a') as f:
                writer = ndjson.writer(f)
                writer.writerow(content)

            '''with open('./guild_ndjson/' + file) as f:
                read_data = ndjson.load(f)'''

            print("Success!:" + template_name + "として入力された内容を保存しました。")
            if language == "ja":
                embed=discord.Embed(title="成功しました!", description=template_name + "として入力された内容を保存しました。", color=0x00ff7f)
            elif language == "en":
                embed=discord.Embed(title="Success!", description="Saved what was entered as " + template_name + ".", color=0x00ff7f)
            await interaction.followup.send(embed=embed) 
            
        else:
            print("Error!:Not support range!")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:この範囲指定はサポートしていません！:x:", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Not support range!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)
        
    else:
        if spreadsheet_url[0:37] == 'https://docs.google.com/spreadsheets/':
            # debug message start
            print('-Change start-')
            print('')

            print(spreadsheet_url)
            print('')

            url = spreadsheet_url[39:]
            print(url)
            print('')

            id = url.split('/')[0]
            print(id)
            print('')

            print('-Change finish!-')
            print('')
        else:
            # debug message start
            print('-Change start!-')
            print('')

            print('Error!:Not Support Link or No Link!')
            print('')

            print('-Change finish!-')
            print('')
            # debug message finish

            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:このリンクはサポートされていないか、リンクではありません！:x:", color=0xff0000)
            elif language == "en":    
                embed=discord.Embed(title="Error!", description=":x:Not Support Link or No Link!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)
        
        if re.match('[\w][\d]:[\w][\d]', selected_range) or re.match('[\w][\d][\d]:[\w][\d][\d]', selected_range):
            await interaction.response.defer()
            content = {
                "template_name" : template_name,
                "spreadsheet_id": id,
                "sheet_name": sheet_name,
                "selected_range" : selected_range
            }

            # print(interaction.guild.id)

            file = str(interaction.guild.id) + ".ndjson"
            with open('./guild_ndjson/' + file, 'a') as f:
                writer = ndjson.writer(f)
                writer.writerow(content)

            print("Success!:" + template_name + "として入力された内容を保存しました。")
            if language == "ja":
                embed=discord.Embed(title="成功しました!", description=template_name + "として入力された内容を保存しました。", color=0x00ff7f)
            elif language == "en":
                embed=discord.Embed(title="Success!", description="Saved what was entered as " + template_name + ".", color=0x00ff7f)
            await interaction.followup.send(embed=embed) 
            
        else:
            print("Error!:Not support range!")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description=":x:この範囲指定はサポートしていません！:x:", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description=":x:Not support range!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)

# /sstemplate_delete
@tree.command(name="sstemplate_delete",description="/sstemplate_frで実行するためのテンプレートを削除します。 / Delete to use [/sstemplate_fr] command template.")
async def sstemplate_delete_command(interaction: discord.Interaction,template_name:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./guild_ndjson/*.ndjson')
    judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.guild.id) + ".ndjson"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
    
    if(judge == 1):
        file = str(interaction.guild.id) + ".ndjson"
        with open('./guild_ndjson/' + file) as f:
                read_data = ndjson.load(f)
                
        if len(read_data) == 1:
            os.remove('./guild_ndjson/' + file)
            print("Success!:" + template_name + "を削除しました。また、今回の削除を行ったことでこのサーバーのテンプレートが何もない状態となりました。")
            if language == "ja":
                embed=discord.Embed(title="成功しました!", description=template_name + "を削除しました。\nまた、今回の削除を行ったことでこのサーバーのテンプレートが何もない状態となりました。", color=0x00ff7f)
            elif language == "en":
                embed=discord.Embed(title="Success!", description=template_name + " was deleted. In addition, this deletion has resulted in a blank template for this server.", color=0x00ff7f)     
            await interaction.response.send_message(embed=embed)
        else:
            data_write = 0

            for i in range(0, len(read_data)):
                if template_name == read_data[i]["template_name"]:
                    del read_data[i]
                    data_write = 1
                    break

            if data_write == 1:
                for i in range(0, len(read_data)):
                    with open('./guild_ndjson/' + file, 'a') as f:
                        writer = ndjson.writer(f)
                        writer.writerow(read_data[i])
            
                print("Success!:" + template_name + "を削除しました。")
                if language == "ja":
                    embed=discord.Embed(title="成功しました!", description=template_name + "を削除しました。", color=0x00ff7f)
                elif language == "en":
                        embed=discord.Embed(title="Success!", description=template_name + " was deleted.", color=0x00ff7f)
                await interaction.response.send_message(embed=embed)
            else:
                print("Error!:" + template_name + "は存在しません。")
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description=template_name + "は存在しません。", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description=template_name + " does not exist.", color=0xff0000)
                await interaction.response.send_message(embed=embed)

    else:
        print("Error!:/sstemplate_setコマンドでテンプレート登録を行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="/sstemplate_setコマンドでテンプレート登録を行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="Please use the /sstemplate_set command to register your template.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /sstemplate_list
@tree.command(name="sstemplate_list",description="/sstemplate_frで実行するためのテンプレートの一覧を表示します。 / View list to use [/sstemplate_fr] command template.")
async def sstemplate_delete_command(interaction: discord.Interaction):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./guild_ndjson/*.ndjson')
    judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.guild.id) + ".ndjson"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0

    if(judge == 1):
        file = str(interaction.guild.id) + ".ndjson"
        with open('./guild_ndjson/' + file) as f:
                read_data = ndjson.load(f)
        
        '''if(len(read_data) == 0):
            print("Error!:テンプレートが存在しません。/sstemplate_setコマンドでテンプレート登録を行ってください。")
            embed=discord.Embed(title="Error!", description="テンプレートが存在しません。\n/sstemplate_setコマンドでテンプレート登録を行ってください。", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)'''
        if language == "ja":
            embed=discord.Embed(title="成功しました!", color=0x00ff7f)
        elif language == "en":
            embed=discord.Embed(title="Success!", color=0x00ff7f)
        for i in range(0, len(read_data)):
            if language == "ja":
                embed.add_field(name=read_data[i]["template_name"], value="スプレッドシートURL:" + "https://docs.google.com/spreadsheets/d/"+ read_data[i]["spreadsheet_id"] +"/edit?usp=sharing\nsheet_name:" + read_data[i]["sheet_name"] + "\n範囲:" + read_data[i]["selected_range"], inline=False)
            elif language == "en":
                embed.add_field(name=read_data[i]["template_name"], value="spreadsheet_url:" + "https://docs.google.com/spreadsheets/d/"+ read_data[i]["spreadsheet_id"] +"/edit?usp=sharing\nsheet_name:" + read_data[i]["sheet_name"] + "\nselected_range:" + read_data[i]["selected_range"], inline=False)
        
        with open('./guild_ndjson/' + file, 'w') as f:
                ndjson.dump(read_data, f)
        
        print("データ出力に成功しました！")
        await interaction.response.send_message(embed=embed) 
    else:
        print("Error!:テンプレートが存在しません。/sstemplate_setコマンドでテンプレート登録を行ってください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="テンプレートが存在しません。\n/sstemplate_setコマンドでテンプレート登録を行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="The template does not exist.\nPlease use the /sstemplate_set command to register the template.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /sstemplate_fr
@tree.command(name="sstemplate_fr",description="テンプレート登録してあるスプレッドシートにあるフレンドコードに対してフレンド申請を行います。 / Spreadsheet template friend request.")
async def sstemplate_fr_command(interaction: discord.Interaction,template_name:str):
    # 言語の確認
    file = str(interaction.guild.id) + ".json"

    with open('./language_json/' + file) as f:
        read_data = ndjson.load(f)

    language = read_data[0]["language_mode"]

    files = glob.glob('./user_json/*.json')
    judge = 0
    response_num = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.user.id) + ".json"):
            print("一致しました！")
            judge = 1
            break
        else:
            judge = 0
      
    files = glob.glob('./guild_ndjson/*.ndjson')
    name_judge = 0

    for i in range(0, len(files)):
        print(os.path.split(files[i])[1])
        if(os.path.split(files[i])[1] == str(interaction.guild.id) + ".ndjson"):
            print("ギルドも一致しました！")
            name_judge = 1
            break
        else:
            name_judge = 0
    
    if(name_judge != 1):
        print("Error!:テンプレートが存在しません。\n/sstemplate_setコマンドでテンプレートを設定してください。")
        if language == "ja":
            embed=discord.Embed(title="エラー!", description="テンプレートが存在しません。\n/sstemplate_setコマンドでテンプレート登録を行ってください。", color=0xff0000)
        elif language == "en":
            embed=discord.Embed(title="Error!", description="The template does not exist.\nPlease use the /sstemplate_set command to register the template.", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)
    else:
        if(judge == 1):
            with open('./user_json/' + str(interaction.user.id) + ".json") as f:
                jsn = json.load(f)
            
            if time.time() - jsn["time"]["time"] >= 7200:
                print("Error!:前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。")
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description="It has been two hours since the last authentication.\nPlease execute the /setup_step1 and /setup_step2 commands to authenticate again.", color=0xff0000)
                os.remove("./user_json/" + str(interaction.user.id) + ".json")
                await interaction.response.send_message(embed=embed,ephemeral=False)
                return
  
            web_token = jsn["web_token"]["web_token"]
            allmessage = ""
            message = ""
            
            id = ""
            sheet_name = ""
            selected_range = ""
            file = str(interaction.guild.id) + ".ndjson"

            with open('./guild_ndjson/' + file) as f:
                read_data = ndjson.load(f)
        
            for i in range(0, len(read_data)):
                if template_name == read_data[i]["template_name"]:
                    id = read_data[i]["spreadsheet_id"]
                    sheet_name = read_data[i]["sheet_name"]
                    selected_range = read_data[i]["selected_range"]
                    break

            if re.match('[\w][\d]:[\w][\d]', selected_range) or re.match('[\w][\d][\d]:[\w][\d][\d]', selected_range):
                await interaction.response.defer()

                url = requests.get("https://sheets.googleapis.com/v4/spreadsheets/" + id + "/values/" + sheet_name + "!" + selected_range + "?key=+" + spreadsheet_apikey)
                text = url.text

                data = json.loads(text)

                #codedata = data["values"]
                #print(data["values"])

                codedata = []
                for i in range(0, len(data["values"])):
                    codedata.append(data["values"][i][0])
                
                # print(codedata)
                # num = len(codedata)
                # print(num)
                # print(codedata[0][0])

                for i in range(0, len(codedata)):
                    # def search_friend_code(web_token):
                    friend_code = codedata[i]

                    message = "**" + str(i+1) + ". " + friend_code + "**"
                    if(response_num == 0):
                        allmessage = allmessage + message + "\n"
                        await interaction.followup.send(allmessage)
                        response_num = 1
                    else:
                        allmessage = allmessage + "\n"
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)

                    if re.match('[\d]{4}-[\d]{4}-[\d]{4}$', friend_code):

                        resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/Friend/GetUserByFriendCode", json={
                            "parameter": {
                                "friendCode": friend_code
                            }
                        }, headers={
                            "Content-Type": "application/json; charset=utf-8",
                            "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                            "Authorization": "Bearer {}".format(web_token)
                        })
                        if resp.status_code != 200 or "errorMessage" in resp.json():
                            print("Error searching for friend code, aborting... ({})".format(resp.text))
                            if language == "ja":
                                message = "> エラー! :x:フレンドコードの検索でエラーが発生しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                            elif language == "en":
                                message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                            allmessage = allmessage + message + "\n"
                            await interaction.edit_original_response(content=allmessage)
                            await asyncio.sleep(10)
                            continue
                            #sys.exit(1)
                        print("{}さんにフレンド申請します".format(resp.json()["result"]["name"]))
                        friend_name = resp.json()["result"]["name"]

                        nsaId = resp.json()["result"]["nsaId"]

                        nsa_id = nsaId

                        resp = rsess.post("https://api-lp1.znc.srv.nintendo.net/v3/FriendRequest/Create", json={
                            "parameter": {
                                "nsaId": nsa_id
                            }
                        }, headers={
                            "Content-Type": "application/json; charset=utf-8",
                            "User-Agent": "com.nintendo.znca/2.5.1 (Android/10)",
                            "Authorization": "Bearer {}".format(web_token)
                        })
                        if resp.status_code != 200 or "errorMessage" in resp.json():
                            print("Error sending friend request, aborting... ({})".format(resp.text))
                            if language == "ja":
                                message = "> エラー! :x:フレンドリクエストの送信に失敗しました。:x: ```該当するフレンドコード:" + friend_code + "\n> {}```".format(resp.text)
                            elif language == "en":
                                message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                            allmessage = allmessage + message + "\n"
                            await interaction.edit_original_response(content=allmessage)
                            await asyncio.sleep(10)
                            continue
                            #sys.exit(1)
                        print("フレンド申請を送信しました")
                        if language == "ja":
                            message = "> " + friend_name + "さんにフレンド申請しました！"
                        elif language == "en":
                            message = "> Friend request has been sent to" + friend_name + "!"  
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                    else:
                        print("Error!:Not friend code! friend code:" + friend_code)
                        if language == "ja":
                            message = "> Error! :x:フレンドコードではありません!:x: ```該当するフレンドコード:" + friend_code + "```"
                        elif language == "en":    
                            message = "> Error! :x:Not friend code!:x: ```your typing code:" + friend_code + "```"
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        await asyncio.sleep(10)
                        continue
            else:
                print("Error!:Not support range!")
                if language == "ja":
                    embed=discord.Embed(title="エラー!", description=":x:この範囲指定はサポートしていません！:x:", color=0xff0000)
                elif language == "en":
                    embed=discord.Embed(title="Error!", description=":x:Not support range!:x:", color=0xff0000)
                await interaction.response.send_message(embed=embed,ephemeral=False)
           
            print("Success!:全ての処理が終わりました！")

        else:
            print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
            if language == "ja":
                embed=discord.Embed(title="エラー!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
            elif language == "en":
                embed=discord.Embed(title="Error!", description="First, please use the /setup_step1, /setup_step2 command to set up the system.", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)

client.run(os.environ['token'])