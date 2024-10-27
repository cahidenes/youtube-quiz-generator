import os
from groq import Groq
import re
import dotenv
import yt_dlp

dotenv.load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')


def get_subtitle_data(url, lang_prefixes=('en', 'tr')):
    """
    Extracts subtitles and auto-captions from the result based on language prefixes.
    """
    ydl = yt_dlp.YoutubeDL(params={'quiet': True, 'skip_download': True})
    info = ydl.extract_info(url, download=False)
    sub_keys = [key for key in info.get('subtitles', {}).keys() if key.startswith(lang_prefixes)]
    cap_keys = [key for key in info.get('automatic_captions', {}).keys() if key.startswith(lang_prefixes)]

    subs = {key: info['subtitles'][key] for key in sub_keys}
    auto_captions = {key: info['automatic_captions'][key] for key in cap_keys}

    return sub_keys, cap_keys


def ask_subtitle(sub_keys, cap_keys):
    """
    Displays the available subtitles and auto-captions to the user.
    """
    i = 0
    options = []

    # Display subtitles
    print("Available Subtitles and Auto-captions:")
    print("=======================================")
    print("\n Subtitles:\n")
    for key in sub_keys:
        print(f"[{i}] : {key}")
        options.append(('subtitle', key))
        i += 1
    print("\n Auto-captions:\n")
    for key in cap_keys:
        print(f"[{i}] : {key}")
        options.append(('auto-caption', key))
        i += 1

    max_index = i - 1
    try:
        selected_index = int(input("Select a subtitle or auto-caption by index: "))
    except ValueError:
        print("Error: Please enter a valid number.")
        exit(1)

    if selected_index < 0 or selected_index > max_index:
        print(f"Invalid selection. Please select a number between 0 and {max_index}.")
        exit(1)

    return options[selected_index]


def get_subtitle(url, sub_lang, selected_type):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': [sub_lang],
        'outtmpl': 'subtitle.%(ext)s'
    }
    if selected_type == 'auto-caption':
        ydl_opts['writeautomaticsub'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    with open(f'subtitle.{selected_key}.vtt') as f:
        sub = f.read()

    # parse subtitle
    sep = re.search("^[0-9\\.:]+ --> [0-9\\.:]+.*$", sub, flags=re.MULTILINE)[0]
    i = sub.find(sep)
    l = len(sep)+1

    sub = sub[i+l:]

    text = []
    while sub:
        sep = re.search("^[0-9\\.:]+ --> [0-9\\.:]+.*$", sub, flags=re.MULTILINE)
        if not sep:
            tmp = re.sub("<.*?>", "", sub.replace("\n", "").replace("[Music]", "")).strip()
            if len(text) == 0 or not tmp.startswith(text[-1]) and tmp:
                text.append(tmp)
            break
        sep = sep[0]
        i = sub.find(sep)
        l = len(sep)+1

        tmp = re.sub("<.*?>", "", sub[:i].replace("\n", "").replace("[Music]", "")).strip()
        if len(text) == 0 or not tmp.startswith(text[-1]) and tmp:
            text.append(tmp)
        sub = sub[i+l:]

    text = ' '.join(text)
    return text


def get_questions(text):
    max_len = 19000*4 # API has a limit of 20000 tokens (characters*4 is an approximate for tokens)
    model = 'llama-3.1-8b-instant'

    while text:
        ask = text[:max_len]
        text = text[max_len:]

        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Here is a text: {ask}\n\nWrite 10 short answer questions about important points of this text. Ask for specific answers. Ask to list some points if necessary. Answer each question shortly in curly brackets.",
                }
            ],
            model=model,
        )

        ans = chat_completion.choices[0].message.content
        questions = []
        i = 1
        while True:
            item = f'{i}.'
            ans = ans[ans.find(item) + len(item):]
            q = ans[:ans.find('{')]
            ans = ans[len(q):]
            a = ans[:ans.find('}')+1]
            ans = ans[len(a):]
            if not q or not a:
                break
            questions.append((q.strip(), a.strip().strip('{}')))
            i += 1

        return questions


url = input("Enter url: ")
sub_keys, cap_keys = get_subtitle_data(url)

selected_type, selected_key = ask_subtitle(sub_keys, cap_keys)
print('\nSelected: ' + selected_key + selected_type)

subtitle = get_subtitle(url, selected_key, selected_type)

print('Generating questions...')
questions = get_questions(subtitle)


for i, (question, answer) in enumerate(questions):
    print('\n'*40)
    print(i+1, '/', len(questions))
    print(question)
    print('\n'*15)
    input("Press Enter to see answer...")

    print('\n'*40)
    print(answer)
    print('\n'*15)
    input("Press Enter to see the next question...")
