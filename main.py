import discord, csv, random, os, configparser, sys
from PIL import Image, ImageDraw, ImageFont

OFFSET = 60
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
CHANNEL_ID = 1245842218879815833
global did_win
did_win = False

STRIKE_COLOR = (26, 26, 30, 255)

tosend = ""

def get_from_csv(name):
    toreturn = list()
    with open('data/'+name+'.csv', "r", newline='') as data:
        reader = csv.reader(data)
        next(reader)
        for row in reader:
            toreturn.append(row)
    return toreturn

def get_dict_from_csv(name):
    ls = get_from_csv(name)
    dc = dict()
    for elem in ls:
        dc[elem[0]] = elem[1:]
    return dc

songs = get_from_csv("Music")
global gamedata 
gamedata = get_dict_from_csv("GameData")

def generate_tournament_base(name):
    if not os.path.exists("data/" + name):
        os.mkdir("data/" + name)
    generate_tournament_matches(name, 1, list(range(0,len(songs))))
    exit(1)

def format_id_as_song(id):
    return "[" + songs[id][0] + " - " + songs[id][1] + "](<https://youtu.be/" + songs[id][2] + ">)"

def format_game_as_filename(name):
    name = name.replace('/', '-')
    name = name.replace(':', "#")
    return "data/imgs/" + name + ".avif"

def generate_tournament_matches(name, roundNo, competitors):
    rootpath = "data/" + name + "/"
    print(competitors)

    rounds = list()
    while len(competitors) > 1:
        rounds.append([competitors.pop(random.randrange(len(competitors))), competitors.pop(random.randrange(len(competitors)))])
    if len(competitors) == 1:
        with open(rootpath + "round" + str(roundNo) + "wins.csl", "w") as outfile:
            outfile.write(str(competitors[0]) + ",")
    
    with open(rootpath + "round" + str(roundNo) + ".csv", "w") as outfile:
        for round in rounds:
            for player in round:
                outfile.write(str(player) + ",")
            outfile.seek(outfile.tell() - 1, os.SEEK_SET)
            outfile.write("\n")
    with open(rootpath + "info.ini", "w") as outfile:
        outfile.write("[INFO]\nmatch=-1\nround=" + str(roundNo))


async def progress_tournament(name):

    rootpath = "data/" + name + "/"
    config = configparser.ConfigParser()
    config.read(rootpath + "info.ini")

    match = int(config["INFO"]["match"]) + 1
    round = int(config["INFO"]["round"])

    if match > 0:
        await check_results(name)
    
    with open(rootpath + "round" + str(round) + ".csv", "r", newline='') as round_data:
        roundlist = list(csv.reader(round_data))
    

    winners = list()
    if os.path.exists(rootpath + "round" + str(round) + "wins.csl"):
        with open(rootpath + "round" + str(round) + "wins.csl", "r") as winsfile:
            text = winsfile.read()
            winners = text.split(",")[:-1]

    if len(roundlist) <= match:
        with open(rootpath + "info.ini", "w") as outfile:
            outfile.write("[INFO]\nmatch=" + str(-1) + "\nround=" + str(round+1))

        if len(winners) == 1:
            print(winners)
            song = songs[int(winners[0])]
            global did_win
            did_win = True
            generate_win_img(int(winners[0]))
            return "👑 " + song[0] + " | " + song[1] + " 👑 has been crowned the BEST SONIC BOSS THEME EVERRRRRR!!!!\nThank you all for participating!!!!!"

        generate_tournament_matches(name, round+1, winners)
        return await progress_tournament(name)

    with open(rootpath + "info.ini", "w") as outfile:
        outfile.write("[INFO]\nmatch=" + str(match) + "\nround=" + str(round))

    thisround = roundlist[match]
    generate_img(thisround)

    peopleLeft = (len(roundlist) - match) * 2 + len(winners)
    stringFormat = "Today's Competiton: \n"
    
    if peopleLeft == 2:
        stringFormat += "FINAL ROUND."
    elif len(roundlist) <= 2 and peopleLeft <= 4:
        stringFormat += "SEMI-FINALS"
    else:
        stringFormat += "Round " + str(round)

    stringFormat += " - Match " + str(match+1) + "/" + str(len(roundlist))
    stringFormat += " - " + str(peopleLeft) + " songs remain!\n"

    stringFormat += ":red_circle: " + format_id_as_song(int(thisround[0]))
    stringFormat += "\n"
    stringFormat += ":blue_circle: " + format_id_as_song(int(thisround[1]))

    return stringFormat

async def check_results(name):
    todoEmoji = "🔴"
    with open("lastmessage.id", "r") as id:
        msg = await client.get_channel(CHANNEL_ID).fetch_message(int(id.read()))
        countA = 0
        countB = 0
        for reaction in msg.reactions:
            if reaction.emoji == "🔴":
                countA = reaction.count
            elif reaction.emoji == "🔵":
                countB = reaction.count
        if countA == countB:
            whowon = bool(random.getrandbits(1))
        else:
            whowon = countB > countA
    if whowon:
        todoEmoji = "🔵"

    rootpath = "data/" + name + "/"
    config = configparser.ConfigParser()
    config.read(rootpath + "info.ini")

    match = int(config["INFO"]["match"])
    round = int(config["INFO"]["round"])

    with open("data/bossmusic/round" + str(round) + ".csv", "r", newline='') as round_data:
        roundlist = list(csv.reader(round_data))
    currentRound = roundlist[match]

    winnerID = 0

    with open(rootpath + "round" + str(round) + "wins.csl", "a") as outfile:
        if whowon:
            winnerID = currentRound[1]
        else:
            winnerID = currentRound[0]
        outfile.write(winnerID + ",")
    tosend = "Yesterday's Results:\n" + todoEmoji + " " + songs[int(winnerID)][0] + " | " + songs[int(winnerID)][1] + " won!"
    await client.get_channel(CHANNEL_ID).send(tosend)

def get_wrapped_text(text: str, font: ImageFont.ImageFont,
                     line_length: int):
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return '\n'.join(lines)


def generate_win_img(id):
    song = songs[id]
    img = Image.open(format_game_as_filename(song[1]))
    img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
    draw = ImageDraw.Draw(img)
    fontName = ImageFont.truetype("data/font/NiseSegaSonic.TTF", 48)

    winimg = Image.open("data/imgs/winner.webp").convert("RGBA")
    
    texloc = int(gamedata[song[1]][0]), int(gamedata[song[1]][1])
    draw.text(texloc, get_wrapped_text(song[0], fontName, float(gamedata[song[1]][2])), font=fontName, fill="white", anchor="ma", stroke_width=5, stroke_fill=STRIKE_COLOR, align="center")

    imgf = img.convert("RGBA")

    imgf.alpha_composite(winimg)
    imgf.save("attatchment.png")

def generate_img(round):
    song1 = songs[int(round[0])]
    song2 = songs[int(round[1])]

    im1 = Image.open(format_game_as_filename(song1[1]))
    im2 = Image.open(format_game_as_filename(song2[1]))

    im1 = im1.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
    im2 = im2.resize((IMAGE_WIDTH, IMAGE_HEIGHT))

    im1f = Image.new("RGBA", ((IMAGE_WIDTH*2) - (OFFSET * 2), IMAGE_HEIGHT), (0,0,0,0))
    im2f = im1f.copy()

    im1f.paste(im1)
    im2f.paste(im2, (IMAGE_WIDTH - OFFSET*2, 0))

    draw1 = ImageDraw.Draw(im1f)
    draw2 = ImageDraw.Draw(im2f)

    STRIKE_TOP = (IMAGE_WIDTH,-5)
    STRIKE_BOTTOM = (IMAGE_WIDTH-OFFSET*2, IMAGE_HEIGHT+5)

    draw1.polygon([STRIKE_TOP, STRIKE_BOTTOM, im1f.size, (im1f.width, 0)], fill=(0,0,0,0))
    draw1.line([STRIKE_TOP, STRIKE_BOTTOM], fill=STRIKE_COLOR, width=10)
    im2f.alpha_composite(im1f)

    fontVS = ImageFont.truetype("data/font/LEMONMILK-Medium.otf", 72)
    draw2.text((IMAGE_WIDTH - OFFSET,IMAGE_HEIGHT / 2), "VS", font=fontVS, fill="white", anchor="mm", stroke_width=8, stroke_fill=STRIKE_COLOR)

    fontName = ImageFont.truetype("data/font/NiseSegaSonic.TTF", 48)
    tex1loc = int(gamedata[song1[1]][0]), int(gamedata[song1[1]][1])
    tex2loc = (IMAGE_WIDTH - OFFSET*2) + int(gamedata[song2[1]][0]), int(gamedata[song2[1]][1])

    draw2.text(tex1loc, get_wrapped_text(song1[0], fontName, float(gamedata[song1[1]][2])), font=fontName, fill="white", anchor="ma", stroke_width=5, stroke_fill=STRIKE_COLOR, align="center")

    draw2.text(tex2loc, get_wrapped_text(song2[0], fontName, float(gamedata[song2[1]][2])), font=fontName, fill="white", anchor="ma", stroke_width=5, stroke_fill=STRIKE_COLOR, align="center")

    im2f.save("attatchment.png")

if sys.argv[1] == "generate":
    generate_tournament_base(sys.argv[2])
elif sys.argv[1] == 'imgtest':
    generate_img(0)


class Client(discord.Client):
    async def on_ready(self):
        channel = client.get_channel(CHANNEL_ID)
        tosend = await progress_tournament("bossmusic")
        if len(tosend) != 0:
            sent_message = await channel.send(tosend, file=discord.File("attatchment.png"))
            if did_win:
                exit(2)
            await sent_message.add_reaction("\N{LARGE RED CIRCLE}")
            await sent_message.add_reaction("\N{LARGE BLUE CIRCLE}")


            with open("lastmessage.id", "w") as outfile:
                outfile.write(str(sent_message.id))
            exit(1)
        else:
            print("FAIL")
            exit(-1)
    
intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)

with open("bot.token", "r") as file:
    token = file.read()

client.run(token)
