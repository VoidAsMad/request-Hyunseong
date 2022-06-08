import discord
from pymongo import MongoClient
from discord.ext import commands
from discord.ext import tasks
import datetime

token = 'PUT YOUR TOKEN'
PREFIX = "!"
REASON_TEXT = "블랙리스트 추가 사유를 입력하세요." # 봇 사용자가 수정 해주세요!

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())
server = MongoClient("localhost", 27017)

blacklist = list()

def findInBlacklist(userID, option=""):
    temp = 0
    for i in blacklist:
        if i[1] == userID:
            if option == "remove":
                del blacklist[temp]
            elif option == "search":
                return i
            temp += 1
            return True
    return False

def saveData():
    global blacklist
    collections = server["Data"]["Users"]
    collections.update_one({}, {"$set": {'blacklist': blacklist}})

@bot.command(aliases=['블랙리스트'])
async def blacklist(ctx, value=None, user=None, *reason):
    if not ctx.message.author.guild_permissions.administrator: # 관리자 권한 여부 확인
        await ctx.send("> 관리자 권한이 필요합니다.", reference=ctx.message, mention_author=False)
    elif (value is None or user is None) and value not in ("추가", "삭제", "검색"): # 2개의 인자를 모두 받지 못했다면 + value에 엉뚱한 값을 입력받았을 경우
        await ctx.send(f"> 명령어 도움말 `({PREFIX}블랙리스트 <추가, 삭제, 검색> <닉네임>)`", reference=ctx.message, mention_author=False)
    else:
        if len(user) != 21 and len(user) != 18:
            print(user)
            print(len(user))
            await ctx.send("> 유저 태그(멘션)이 잘못되었습니다.", reference=ctx.message, mention_author=False)
            return
        if len(user) == 21 and "<@" in str(user):
            user = await bot.fetch_user(user[2:-1])
        else:
            user = await bot.fetch_user(user)
        if value == "추가": 
            if findInBlacklist(user.id):
                await ctx.send(f"> 해당 유저는 이미 추가되었습니다.", reference=ctx.message, mention_author=False)
                return
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            reason = ''.join(reason)
            if len(reason) == 0: reason = REASON_TEXT
            blacklist.append([user.name, user.id, reason, now, ctx.author.id])
            saveData()
            await ctx.send(f"> 성공적으로 `{user.name}:{user.id}`을(를) 블랙리스트에 추가했습니다. **(처리 일자: {now})**", reference=ctx.message, mention_author=False)
        elif value == "삭제":
            if findInBlacklist(user.id, "remove"):
                saveData()
                await ctx.send(f"> 성공적으로 `{user.name}:{user.id}`을(를) 블랙리스트에서 삭제되었습니다.", reference=ctx.message, mention_author=False)
            else:
                await ctx.send(f"> 유저 `{user.name}:{user.id}`을(를) 찾지 못했습니다.", reference=ctx.message, mention_author=False)
        elif value == "검색":
            data = findInBlacklist(user.id, "search")
            if type(data) is list:
                embed=discord.Embed(color=0x81c147)
                embed.add_field(name=f"닉네임", value=f"{data[0]}", inline=False)
                embed.add_field(name=f"아이디", value=f"{data[1]}", inline=False)
                embed.add_field(name=f"사유", value=f"{data[2]}", inline=False)
                embed.add_field(name=f"처리 일자", value=f"{data[3]}", inline=False)
                embed.add_field(name=f"처리자", value=f"<@{data[4]}>", inline=False)
                await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            else:
                await ctx.send(f"> 유저 `{user.name}:{user.id}`을(를) 찾지 못했습니다.", reference=ctx.message, mention_author=False)

@bot.event
async def on_ready():
    global blacklist
    collections = server["Data"]["Users"] # 블랙리스트 파일 저장위치
    try:
        blacklist = collections.find_one({}, {'_id': 0})['blacklist']
    except TypeError:
        collections.insert_one({ "blacklist": [] }).inserted_id
        blacklist = collections.find_one({}, {'_id': 0})['blacklist']
    print("The bot is ready.")

bot.run(token)
