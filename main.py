import os
from groq import Groq
import re
import dotenv
import yt_dlp
import json

dotenv.load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ydl_opts = {
        'quiet': True,  # Suppress verbose yt-dlp output
        'skip_download': True,  # Do not download the video'
    }

def get_subtitle_data(result, lang_prefixes=('en', 'tr')):
    """
    Extracts subtitles and auto-captions from the result based on language prefixes.
    """
    sub_keys = [key for key in result.get('subtitles', {}).keys() if key.startswith(lang_prefixes)]
    cap_keys = [key for key in result.get('automatic_captions', {}).keys() if key.startswith(lang_prefixes)]

    subs = {key: result['subtitles'][key] for key in sub_keys}
    auto_captions = {key: result['automatic_captions'][key] for key in cap_keys}

    return subs, auto_captions, sub_keys, cap_keys

def display_options(sub_keys, cap_keys):
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

    # Display auto-captions
    print("\n Auto-captions:\n")
    for key in cap_keys:
        print(f"[{i}] : {key}")
        options.append(('auto-caption', key))
        i += 1

    return options

def validate_selection(selected_index, max_index):
    """
    Validates the user's input to ensure it falls within the allowed range.
    """
    if selected_index < 0 or selected_index > max_index:
        print(f"Invalid selection. Please select a number between 0 and {max_index}.")
        exit(1)

def download_subtitle(url, sub_lang, selected_type):
    """
    Downloads the selected subtitle or auto-caption.
    """

    ydl_opts = {
        'skip_download': True,                  # don't download the video
        'writesubtitles': True,                 # downloads subtitles
        'subtitleslangs': [sub_lang],           # sets subtitle language
        'subtitlesformat': 'json3',             # sets subtitle format to JSON3
        'outtmpl': 'subtitle.%(ext)s'           # sets the output file name
    }
    
    # Adjust option for automatic subtitles
    if selected_type == 'auto-caption':
        ydl_opts['writeautomaticsub'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

ydl = yt_dlp.YoutubeDL(params=ydl_opts)

url = input("Enter url: ")

result = ydl.extract_info(url, download=False)
# Get subtitles and auto-captions
subs, auto_captions, sub_keys, cap_keys = get_subtitle_data(result)
# Display options
options = display_options(sub_keys, cap_keys)
# Prompt user to select
try:
    selected_index = int(input("Select a subtitle or auto-caption by index: "))
except ValueError:
    print("Error: Please enter a valid number.")
    exit(1)
# Validate selection
validate_selection(selected_index, len(options) - 1)

# Check if the selection is a subtitle or auto-caption
selected_type, selected_key = options[selected_index]
selected_sub = None
if selected_type == 'subtitle':
    print(f"\nSelected Subtitle: {selected_key}")
    selected_sub = subs[selected_key]
else:
    print(f"\nSelected Auto-caption: {selected_key}")
    selected_sub = auto_captions[selected_key]

print('\nSelected subtitle: ' + selected_key + (' subtitle' if selected_type == "subtitle" else ' Auto-caption'))

# Download the selected subtitle
download_subtitle(url, selected_key, selected_type)

# Open the json3 subtitle file
with open(f'subtitle.{selected_key}.json3') as f:
    json_str = json.load(f)

sublen = len(json_str['events'])
text = ""

# iterate through the json3 file and extract the captions
for i in range(sublen):
    try:
        text += json_str['events'][i]['segs'][0]['utf8'].replace("\n", " ")
    except KeyError:
        pass

print('Generating questions...')

max_len = 17000*4 # API has a limit of 18000 tokens (characters*4 is an approximate for tokens)
model = 'llama-3.1-70b-versatile'

while text:
    ask = text[:max_len]
    text = text[max_len:]

    client = Groq(api_key=GROQ_API_KEY)
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
