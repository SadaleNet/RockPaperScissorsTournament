#Command to be executed:
#FLASK_APP=rps.py python3 -m flask run
#Debug mode:
#FLASK_DEBUG=1 FLASK_APP=rps.py python3 -m flask run
import flask
import flask_wtf.csrf
import PIL, PIL.Image, PIL.ImageFont, PIL.ImageDraw
import uuid, datetime, pytz, os, sqlite3, re, time, io, os
import sqlite3
import captcha


app = flask.Flask(__name__)
app.secret_key = "RkBmM9ohIMfoU9t2Zka5Krl/waV5E42+a3n" #TODO: generate one if not exist

EVENT_TITLE = os.getenv("RPS_EVENT_TITLE", "International Asynchronous Rock Paper Scissors Tournament")
app.config['START_TIME'] = datetime.datetime.fromtimestamp(
    int(
        os.getenv("RPS_START_TIME",
        datetime.datetime.now().timestamp()
        )
    )
)

app.config['END_TIME'] = datetime.datetime.fromtimestamp(
    int(
        os.getenv("RPS_END_TIME",
                (app.config['START_TIME']+datetime.timedelta(days=1))
                .timestamp()
            )
        )
    )

app.config['DATABASE_NAME'] = 'data/rps.db'

csrf = flask_wtf.csrf.CSRFProtect(app)
csrf.init_app(app)

@app.route('/')
def page_index():
    return flask.render_template('index.html', event_title=EVENT_TITLE, start_datetime=app.config['START_TIME'], end_datetime=app.config['END_TIME'])

@app.route('/about')
def page_about():
    return flask.render_template('about.html', event_title=EVENT_TITLE)


@app.route('/join')
def page_join():
    if datetime.datetime.now() < app.config['START_TIME']:
        return flask.render_template('join_not_started.html', event_title=EVENT_TITLE, start_datetime=app.config['START_TIME'])
    elif datetime.datetime.now() > app.config['END_TIME']:
        return flask.render_template('join_ended.html', event_title=EVENT_TITLE)
    else:
        return flask.render_template('join.html', event_title=EVENT_TITLE, captcha_id=captcha.generate_new_captcha())

@app.route('/result')
def page_result():
    if datetime.datetime.now() <= app.config['END_TIME']:
        return flask.render_template('result_not_ended.html', event_title=EVENT_TITLE, end_datetime=app.config['END_TIME'])
    conn = sqlite3.connect(app.config['DATABASE_NAME'])
    cur = conn.cursor()
    player = cur.execute("SELECT country, nick, score+cheat, cheat, played FROM game ORDER BY score+cheat DESC").fetchall()
    conn.close()
    playersData = []
    rank = 1
    for row in player:
        playersData.append({'i': rank, 'country': row[0], 'nick': row[1], 'score': row[2], 'cheat': row[3], 'played': row[4]})
        rank += 1
    return flask.render_template('result.html', event_title=EVENT_TITLE, players=playersData)

@app.route('/action', methods=['POST'])
def page_action():
    if datetime.datetime.now() < app.config['START_TIME'] or datetime.datetime.now() > app.config['END_TIME']:
        return flask.redirect("/", code=302)

    COUNTRY_CODE = ["af", "ax", "al", "dz", "as", "ad", "ao", "ai", "ag", "ar", "am", "aw", "au", "at", "az", "bs", "bh", "bd", "bb", "by", "be", "bz", "bj", "bm", "bt", "bo", "ba", "bw", "bv", "br", "vg", "bn", "bg", "bf", "ar", "bi", "tc", "kh", "cm", "ca", "cv", "ky", "cf", "td", "cl", "cn", "cx", "cc", "co", "km", "cg", "cd", "ck", "cr", "ci", "hr", "cu", "cy", "cz", "dk", "dj", "dm", "do", "ec", "eg", "sv", "gb", "gq", "er", "ee", "et", "eu", "fk", "fo", "fj", "fi", "fr", "gf", "pf", "tf", "ga", "gm", "ge", "de", "gh", "gi", "gr", "gl", "gd", "gp", "gu", "gt", "gw", "gn", "gy", "ht", "hm", "hn", "hk", "hu", "is", "in", "io", "id", "ir", "iq", "ie", "il", "it", "jm", "jp", "jo", "kz", "ke", "ki", "kw", "kg", "la", "lv", "lb", "ls", "lr", "ly", "li", "lt", "lu", "mo", "mk", "mg", "mw", "my", "mv", "ml", "mt", "mh", "mq", "mr", "mu", "yt", "mx", "fm", "md", "mc", "mn", "me", "ms", "ma", "mz", "na", "nr", "np", "an", "nl", "nc", "pg", "nz", "ni", "ne", "ng", "nu", "nf", "kp", "mp", "no", "om", "pk", "pl", "pw", "ps", "pa", "py", "pe", "ph", "pn", "pt", "pr", "qa", "re", "ro", "ru", "rw", "sh", "kn", "lc", "pm", "vc", "ws", "sm", "gs", "st", "sa", "sn", "cs", "rs", "sc", "sl", "sg", "sk", "si", "sb", "so", "za", "kr", "es", "lk", "sd", "sr", "sj", "sz", "se", "ch", "sy", "tw", "tj", "tz", "th", "tl", "tg", "tk", "to", "tt", "tn", "tr", "tm", "tv", "ug", "ua", "ae", "us", "uy", "um", "vi", "uz", "vu", "va", "ve", "vn", "wf", "eh", "ye", "zm", "zw"]


    conn = sqlite3.connect(app.config['DATABASE_NAME'])
    cur = conn.cursor()
    player = cur.execute("SELECT * FROM game WHERE nick = ?", (flask.request.form['nick'],)).fetchone()
    current_captcha = captcha.fetch_captcha_answer(flask.request.form['captcha_id'])
    old_captcha = ''
    nick_error = ''
    country_error = ''
    played_error = ''
    captcha_error = ''
    nick_error_type = ''
    played_error_type = ''
    if player != None:
        nick_error = 'error'
        nick_error_type = 1
    elif len(flask.request.form['nick']) == 0:
        nick_error = 'error'
        nick_error_type = 2
    elif len(flask.request.form['nick']) > 32:
        nick_error = 'error'
        nick_error_type = 3
    if flask.request.form['country'] not in COUNTRY_CODE:
        country_error = 'error'
    if len(flask.request.form['played']) != 50:
        played_error = 'played'
        played_error_type = 1
    elif not re.compile('^[rps]{50}$').match(flask.request.form['played']):
        played_error = 'played'
        played_error_type = 2
    elif flask.request.form['played'].find("rrrrrr") != -1 or flask.request.form['played'].find("pppppp") != -1 or flask.request.form['played'].find("ssssss") != -1:
        played_error = 'played'
        played_error_type = 3
    if current_captcha == None or flask.request.form['captcha'] != current_captcha:
        #Wrong captcha. Generating a new captcha
        captcha_error = 'error'
    else:
        old_captcha = flask.request.form['captcha']
    if nick_error or country_error or played_error or captcha_error:
        return flask.render_template('join.html',
            event_title=EVENT_TITLE,
            captcha_id=captcha.generate_new_captcha(),
            nick_error=nick_error,
            country_error=country_error,
            played_error=played_error,
            captcha_error=captcha_error,
            nick_error_type=nick_error_type,
            played_error_type=played_error_type,
            old_nick=flask.request.form['nick'],
            old_country=flask.request.form['country'],
            old_played=flask.request.form['played'],
            )

    player = cur.execute("SELECT pk, played FROM game").fetchall()
    newPlayerScore = 0
    for i in player:
        pk, played = i
        existingPlayerScoreAdjustment = 0
        for j in range(len(flask.request.form['played'])):
            if (flask.request.form['played'][j] == 'r' and played[j] == 's'
                or flask.request.form['played'][j] == 's' and played[j] == 'p'
                or flask.request.form['played'][j] == 'p' and played[j] == 'r'):
                newPlayerScore += 1
                existingPlayerScoreAdjustment -= 1
            elif (flask.request.form['played'][j] == 'r' and played[j] == 'p'
                or flask.request.form['played'][j] == 's' and played[j] == 'r'
                or flask.request.form['played'][j] == 'p' and played[j] == 's'):
                newPlayerScore -= 1
                existingPlayerScoreAdjustment += 1
        cur.execute("UPDATE game SET score = score + ? WHERE pk = ?", (existingPlayerScoreAdjustment,pk,))
    cur.execute("INSERT INTO game (nick, country, played, cheat, score) VALUES (?, ?, ?, ?, ?)",
        (flask.request.form['nick'], flask.request.form['country'], flask.request.form['played'], 
        0, newPlayerScore))
    captcha.invalidate(flask.request.form['captcha_id'])
    conn.commit()
    conn.close()
    return flask.redirect("/done", code=302)

@app.route('/done')
def page_done():
    if datetime.datetime.now() < app.config['START_TIME'] or datetime.datetime.now() > app.config['END_TIME']:
        return flask.redirect("/", code=302)
    return flask.render_template('done.html', event_title=EVENT_TITLE, end_datetime=app.config['END_TIME'])

@app.route('/captcha/<int:captcha_id>')
def page_captcha(captcha_id):
    return flask.send_file(captcha.get_captcha_path(captcha_id), mimetype='image/png', cache_timeout=-1)

@app.route('/certificate/<nick>')
def page_certificate(nick):
    #Check if the tournament has ended.
    if datetime.datetime.now() <= app.config['END_TIME']:
        return flask.redirect("/", code=302)
    #Check if the nick had joined the tournament
    conn = sqlite3.connect(app.config['DATABASE_NAME'])
    cur = conn.cursor()
    player = cur.execute("SELECT * FROM game WHERE nick = ?", (nick,)).fetchone()
    conn.close()
    if player == None:
        return flask.redirect("/", code=302)
    #Generate the certificate
    base = PIL.Image.open("certificate.png").convert('RGBA')
    overlay = PIL.Image.new('RGBA', base.size, (255,255,255,0))
    font = PIL.ImageFont.truetype('Tuffy.ttf', 50)
    draw = PIL.ImageDraw.Draw(overlay)
    textW, textH = draw.textsize(nick, font=font)
    textX, textY = int(os.getenv("RPS_CERT_NAME_X", "744")), int(os.getenv("RPS_CERT_NAME_Y", "1060"))
    draw.text((textX-textW/2,textY-textH), nick, font=font, fill=(0,0,0,255))
    out = PIL.Image.alpha_composite(base, overlay)
    outputImage = io.BytesIO()
    out.save(outputImage, 'PNG')
    outputImage.seek(0)
    return flask.send_file(outputImage, mimetype='image/png', cache_timeout=-1)

#Setup sqlite database
def setup_db():
    if not os.path.exists(app.config['DATABASE_NAME']):
        conn = sqlite3.connect(app.config['DATABASE_NAME'])
        conn.execute("CREATE TABLE game (pk integer primary key, nick text unique, country text, played text, cheat integer, timestamp integer default CURRENT_TIMESTAMP, score integer)")
        conn.commit()
        conn.close()
        captcha.setup_db()

if __name__ == "__main__":
    setup_db()
