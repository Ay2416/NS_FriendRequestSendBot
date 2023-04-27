# Discord bot import
import discord
from discord import app_commands
from discord import ui
import os
from dotenv import load_dotenv
from time import sleep
from mk8dx import lounge_api
import glob
#import ndjson
import time

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
    await client.change_presence(activity=discord.Game(name="Ver.1.0 | /help"))
    await tree.sync()#スラッシュコマンドを同期
    print("グローバルコマンド同期完了！")
    
    # setup_json, user_jsonフォルダがあるかの確認
    files = glob.glob('./*')

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

# /test
@tree.command(name="test",description="テストコマンドです。")
async def test_command(interaction: discord.Interaction,text:str):
    await interaction.response.defer(ephemeral=False)

    await interaction.followup.send("> " + text + "\n> " + text)

# /setup_step1
@tree.command(name="setup_step1",description="ニンテンドーアカウント認証用のリンクを作ります。")
async def setup_step1(interaction: discord.Interaction):

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
    
    embed=discord.Embed(title="こちらでニンテンドーアカウントにログインしてください。", color=0xffffff)
    embed.add_field(name="・ログインしましたら、", value="　", inline=False)
    embed.add_field(name="パソコンの場合", value="「この人にする」ボタンを右クリックし「リンクアドレスをコピー」を選択して/setup_step2コマンドの[link_address]の部分でペーストしてください。", inline=False)
    embed.add_field(name="スマホの場合", value="「この人にする」ボタンを長押しして、「リンクアドレスをコピー」を選択して/setup_step2コマンドの[link_address]に部分でペーストしてください。", inline=False)
    embed.add_field(name="⇩URL⇩", value=oauth_uri, inline=False)
    await interaction.response.send_message(embed=embed,ephemeral=True)

# /setup_step2
@tree.command(name="setup_step2",description="/setup_step1のリンクアドレスを貼り付け、セットアップを開始します。")    
async def setup_step2(interaction: discord.Interaction, link_address:str):
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
            embed=discord.Embed(title="Error!", description=":x:Invalid redirect URI, aborting...:x:", color=0xff0000)
            await interaction.followup.send(embed=embed)
            return
            #sys.exit(1)

        session_state = redirect_uri_parsed[0]
        session_token_code = redirect_uri_parsed[1]
        response_state = redirect_uri_parsed[2]

        if state != response_state:
            print("Invalid redirect URI (bad OAuth state), aborting...")
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
            "User-Agent": "OnlineLounge/2.5.0 NASDKAPI Android"
        })
        if resp.status_code != 200:
            print("Error obtaining session token from Nintendo, aborting... ({})".format(resp.text))
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
            "User-Agent": "OnlineLounge/2.5.0 NASDKAPI Android"
        })
        if resp.status_code != 200:
            print("Error obtaining service token from Nintendo, aborting... ({})".format(resp.text))
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
            "User-Agent": "OnlineLounge/2.5.0 NASDKAPI Android",
            "Authorization": "Bearer {}".format(access_token)
        })
        if resp.status_code != 200:
            print("Error obtaining account data from Nintendo, aborting... ({})".format(resp.text))
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
            "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
            "X-ProductVersion": "2.5.0",
            "X-Platform": "Android"
        })

        if resp.status_code != 200 or "errorMessage" in resp.json():
            print("Error logging into Switch API, aborting... ({})".format(resp.text))
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
        embed=discord.Embed(title="Success!", description="認証成功！\n2時間後に認証が切れてしまいますのでそれ以上使う場合はもう1度/setup_step1,/setup_step2コマンドを実行してください。", color=0x00ff40)
        await interaction.followup.send(embed=embed)
    else:
        print("Error!:最初に/setup_step1コマンドでセットアップを行ってください。")
        embed=discord.Embed(title="Error!", description="最初に/setup_step1コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /finish
@tree.command(name="finish",description="フレンド申請のプログラムを終了させます。")
async def finish(interaction: discord.Interaction):
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
        embed=discord.Embed(title="終了処理が完了しました！", description="また使う際は、/setup_step1,/setup_step2コマンドを行ってからご使用ください！", color=0x00ff40)
        await interaction.response.send_message(embed=embed)
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        embed=discord.Embed(title="Error!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /help
@tree.command(name="help",description="コマンドについての簡単な使い方を出します。")
async def help(interaction: discord.Interaction):
        embed=discord.Embed(title="Command list")
        embed.add_field(name="/setup_step1", value="このBotを使うに当たってセットアップに必要な任天堂アカウントログイン用のURLを発行します。", inline=False)
        embed.add_field(name="/setup_step2 [/setup_step1でコピーをしたURL]", value="このBotを使うに当たってセットアップに必要なセットアップを完了させます。", inline=False)
        embed.add_field(name="/finish", value="このBotでの処理を終了し、セットアップが必要な初期状態に戻します。\n（※使い終わったら必ず実行してください。次回以降の使用に影響が出る可能性があります。）", inline=False)
        embed.add_field(name="/help", value="このBotのコマンドの簡単な使い方を出します。", inline=False)
        embed.add_field(name="/server_num", value="このBotの導入されているサーバー数を表示します。", inline=False)
        embed.add_field(name="/fr [SWを除くフレンドコード（例：1234-5678-9012）]", value="セットアップしたアカウントから指定のフレンドコードに対して、フレンド申請を行います。「,」で区切ることで複数人に対してフレンド申請を送ることが可能です。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="/lounge_fr [MK8DXラウンジ名]", value="セットアップしたアカウントから入力されたMK8DXラウンジ名の人に対して、フレンド申請を行います。「,」で区切ることで複数人に対してフレンド申請を送ることが可能です。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        embed.add_field(name="/spreadsheet_fr [共有リンク] [シート名] [範囲（Excelの「○○:○○」の指定方法に準ずる）]", value="セットアップしたアカウントからスプレッドシートの指定された範囲のフレンドコードに対してフレンド申請を行います。\nフレンドコードはSWを除く形（例：1234-5678-9012）で書いてください。\n（※/setup_step1,/setup_step2を完了後に使用可能）", inline=False)
        # embed.set_footer(text="※こちらから詳しい使い方を確認してください!↓\nhttps://ay2416.github.io/NSO-FriendRequestSendBot/")
        embed.add_field(name="※こちらから詳しい使い方を確認してください!↓", value="https://ay2416.github.io/NSO-FriendRequestSendBot/", inline=False)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /server_num
@tree.command(name="server_num",description="導入されているサーバー数を取得します。")
async def server_num(interaction: discord.Interaction):
        embed=discord.Embed(title="導入サーバー数", description=str(len(client.guilds)) + " サーバー")
        
        await interaction.response.send_message(embed=embed)

# /fr
@tree.command(name="fr",description="フレンドコードからフレンド申請を行います。")
async def fr_command(interaction: discord.Interaction,code:str):
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
                embed=discord.Embed(title="Error!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
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
                    "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error searching for friend code, aborting... ({})".format(resp.text))
                    message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
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
                    "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error sending friend request, aborting... ({})".format(resp.text))
                    message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing code:" + friend_code + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
                    continue
                    #sys.exit(1)
                print("フレンド申請を送信しました")
                message = "> " + friend_name + "さんにフレンド申請しました！"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                sleep(10)
            else:
                print("Error!:Not friend code! your typing code:" + friend_code)
                message = "> Error! :x:Not friend code!:x: ```your typing code:" + friend_code + "\n```"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                sleep(10)
                continue

        print("Success!:全ての処理が終わりました！")
    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        embed=discord.Embed(title="Error!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

# /lounge_fr
@tree.command(name="lounge_fr",description="MK8DXラウンジの名前からフレンド申請を行います。")
async def lounge_fr_command(interaction: discord.Interaction,lounge_name:str):
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
            embed=discord.Embed(title="Error!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
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
                    "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error searching for friend code, aborting... ({})".format(resp.text))
                    message = "> Error! :x:Error searching for friend code, aborting...:x: ```your typing lounge name:" + name_data[i] + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
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
                    "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                    "Authorization": "Bearer {}".format(web_token)
                })
                if resp.status_code != 200 or "errorMessage" in resp.json():
                    print("Error sending friend request, aborting... ({})".format(resp.text))
                    message = "> Error! :x:Error sending friend request, aborting...:x: ```your typing lounge name:" + name_data[i] + "\n> {}```".format(resp.text)
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
                    continue
                    #sys.exit(1)
                print("フレンド申請を送信しました")
                message = "> " + friend_name + "さんにフレンド申請しました！"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                sleep(10)
            else:
                print("Error!:Not friend code! your typing lounge name Not found!:" + name_data[i])
                message = "> Error! :x:Not friend code!:x: ```your typing lounge name Not found!:" + name_data[i] + "\n> ```"
                allmessage = allmessage + message + "\n"
                await interaction.edit_original_response(content=allmessage)
                sleep(10)
                continue
        
        print("Success!:全ての処理が終わりました！")
    else:
        embed=discord.Embed(title="Error!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)
        #await interaction.response.send_message("test message",ephemeral=False)

# /spreadsheet_fr
@tree.command(name="spreadsheet_fr",description="スプレッドシートの指定の範囲にあるフレンドコードに対してフレンド申請を行います。")
async def spreadsheet_fr_command(interaction: discord.Interaction,spreadsheet_url:str,sheet_name:str,selected_range:str):
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
            embed=discord.Embed(title="Error!", description="前回の認証から2時間たってしまいました。\n再度認証が必要ですので、/setup_step1,/setup_step2コマンドの実行をお願いします。", color=0xff0000)
            os.remove("./user_json/" + str(interaction.user.id) + ".json")
            await interaction.response.send_message(embed=embed,ephemeral=False)
            return

        web_token = jsn["web_token"]["web_token"]
        spreadsheet_apikey = "your_api_key"
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
                        "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error searching for friend code, aborting... ({})".format(resp.text))
                        message = "> Error! :x:Error searching for friend code, aborting...:x: ```friend code:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        sleep(10)
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
                        "User-Agent": "com.nintendo.znca/2.5.0 (Android/10)",
                        "Authorization": "Bearer {}".format(web_token)
                    })
                    if resp.status_code != 200 or "errorMessage" in resp.json():
                        print("Error sending friend request, aborting... ({})".format(resp.text))
                        message = "> Error! :x:Error sending friend request, aborting...:x: ```friend code:" + friend_code + "\n> {}```".format(resp.text)
                        allmessage = allmessage + message + "\n"
                        await interaction.edit_original_response(content=allmessage)
                        sleep(10)
                        continue
                        #sys.exit(1)
                    print("フレンド申請を送信しました")
                    message = "> " + friend_name + "さんにフレンド申請しました！"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
                else:
                    print("Error!:Not friend code! friend code:" + friend_code)
                    message = "> Error! :x:Not friend code!:x: ```friend code:" + friend_code + "```"
                    allmessage = allmessage + message + "\n"
                    await interaction.edit_original_response(content=allmessage)
                    sleep(10)
                    continue
        else:
            print("Error!:Not Support!")
            embed=discord.Embed(title="Error!", description=":x:Not Support!:x:", color=0xff0000)
            await interaction.response.send_message(embed=embed,ephemeral=False)

        print("Success!:全ての処理が終わりました！")

    else:
        print("Error!:最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。")
        embed=discord.Embed(title="Error!", description="最初に/setup_step1,/setup_step2コマンドでセットアップを行ってください。", color=0xff0000)
        await interaction.response.send_message(embed=embed,ephemeral=False)

client.run(os.environ['token'])