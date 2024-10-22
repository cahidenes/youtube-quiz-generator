import os
from groq import Groq
import re

url = input("Enter url: ")

print('Fetching available subtitles...')
os.system('yt-dlp --list-subs ' + url + ' > sublist.txt')
s = open('sublist.txt').read()

autos = []
subs = []

counter = 0
for line in s.splitlines():
    if line.startswith('[info]') or line.startswith('Language'):
        counter += 1
    else:
        if counter == 2:
            if line.startswith('en') or line.startswith('tr'):
                autos.append(line.split()[0])
        if counter == 4:
            subs.append(line.split()[0])

print('-- Available Subtitles --')
print('Auto-generated:')
print('\n'.join(f'[{number}] {name}' for number, name in enumerate(autos)))
print('Manual:')
print('\n'.join(f'[{number}] {name}' for number, name in zip(range(len(autos), len(autos)+len(subs)), subs)))
print()

selection = input('Selection: ')
try:
    selection = int(selection)
    if selection < len(autos):
        sub = autos[selection]
        auto = True
    else:
        sub = subs[selection-len(autos)]
        auto = False
except:
    print('Invalid selection')
    exit(1)

print('Selected subtitle: ' + sub + (' Auto-generated' if auto else ' Manual'))

if auto:
    os.system(f'yt-dlp --write-auto-sub --sub-lang {sub} --skip-download -o "subtitle.%(ext)s" {url}')
else:
    os.system(f'yt-dlp --write-sub --sub-lang {sub} --skip-download -o "subtitle.%(ext)s" {url}')

with open(f'subtitle.{sub}.vtt') as f:
    sub = f.read()


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

print('Generating questions...')

max_len = 17000*4 # API has a limit of 18000 tokens (characters*4 is an approximate for tokens)
model = 'llama-3.1-70b-versatile'
api_key = open('api_key.txt').read().strip()

while text:
    ask = text[:max_len]
    text = text[max_len:]

    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Here is a text: {ask}\n\nWrite 10 short answer questions about important points of this text. Ask for specific answers. Ask to list some points if necessary. Answer each question shortly in parentheses.",
            }
        ],
        model=model,
    )

    match = re.search(
            r"1. ?(.*?)\s*\((.*?)\)\s*2. ?(.*?)\s*\((.*?)\)\s*3. ?(.*?)\s*\((.*?)\)\s*4. ?(.*?)\s*\((.*?)\)\s*5. ?(.*?)\s*\((.*?)\)\s*6. ?(.*?)\s*\((.*?)\)\s*7. ?(.*?)\s*\((.*?)\)\s*8. ?(.*?)\s*\((.*?)\)\s*9. ?(.*?)\s*\((.*?)\)\s*10. ?(.*?)\s*\((.*?)\)",
            chat_completion.choices[0].message.content,
            flags=re.MULTILINE
            )
    if not match:
        print("Error parsing")
        print(chat_completion.choices[0].message.content)
        break

    index = 1
    while index < 20:
        print('\n'*40)
        print(match[index])
        print('\n'*15)
        input("Press Enter to see answer...")
        index += 1

        print('\n'*40)
        print(match[index])
        print('\n'*15)
        input("Press Enter to see the next question...")
        index += 1
