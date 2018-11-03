import flask, os, random, sqlite3
import PIL, PIL.Image, PIL.ImageFont, PIL.ImageDraw

DATABASE_NAME = './data/captcha.db'
CAPTCHA_DIR = './data/captcha/'

def fetch_captcha_answer(captcha_id):
    conn = sqlite3.connect(DATABASE_NAME)
    ret = conn.execute("SELECT answer FROM captcha WHERE pk = ?", (captcha_id,)).fetchone()
    conn.commit()
    conn.close()
    return None if ret == None else ret[0]

def generate_new_captcha():
    AVAILABLE_CHAR = '34568bcefhjkmnprstuvwxy'
    STRING_LENGTH = 8
    captchaString = ''.join(
        [ AVAILABLE_CHAR[random.randint(0, len(AVAILABLE_CHAR)-1)] for i in range(STRING_LENGTH) ]
    )
    
    #Save the captcha into database
    conn = sqlite3.connect(DATABASE_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO captcha (answer) VALUES (?)", (captchaString,))
    captcha_id = cur.lastrowid
    conn.commit()
    conn.close()
    #Crete the captcha image
    WIDTH, HEIGHT = 180, 30
    im = PIL.Image.new('RGBA', (WIDTH, HEIGHT))
    #fnt = PIL.ImageFont.load_default()
    fnt = PIL.ImageFont.truetype('Tuffy.ttf', 20)
    draw = PIL.ImageDraw.Draw(im)
    #draw the characters
    for i in range(len(captchaString)):
        c = captchaString[i]
        draw.text((10+i*20+random.randint(-5,5),random.randint(0,8)),
            c, font=fnt,
            fill=(0, 0, 0)
        )
    #draw a horizontal line
    draw.line(
        xy=[(random.randint(0,WIDTH//4),random.randint(HEIGHT//4,HEIGHT*3//4)),
        (random.randint(WIDTH*3//4,WIDTH),random.randint(HEIGHT//4,HEIGHT*3//4))],
        fill=(0, 0, 0),
        width=random.randint(1,2)
    )
    del draw

    #write the file to the model
    im.save(os.path.join(CAPTCHA_DIR, '{}.png'.format(captcha_id)), 'PNG')
    return captcha_id

#Warning: This does not check if the captcha path actually exists.
#If the file is missing, we'd just let the web server to send out the HTTP 404
def get_captcha_path(captcha_id):
    return os.path.join(CAPTCHA_DIR, '{}.png'.format(captcha_id))

def invalidate(captcha_id):
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("DELETE FROM captcha WHERE pk = ?", (captcha_id,))
    conn.commit()
    conn.close()
    os.remove(get_captcha_path(captcha_id))


#Setup sqlite database
def setup_db():
    if not os.path.exists(DATABASE_NAME):
        conn = sqlite3.connect(DATABASE_NAME)
        conn.execute("CREATE TABLE captcha (pk integer primary key, answer text, used integer default 0)")
        conn.commit()
        conn.close()
    if not os.path.exists(CAPTCHA_DIR):
        os.mkdir(CAPTCHA_DIR, mode=0o755)
