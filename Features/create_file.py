def get_file_extension(text):
    # Detect file extension from text command

    if "python file" in text:
        text = text.replace("python file","")
        ex = ".py"

    elif "java file" in text:
        text = text.replace("java file","")
        ex = ".java"

    elif "c file" in text:
        ex = ".c"

    elif "c plus plus file" in text or "cpp file" in text:
        ex = ".cpp"

    elif "c sharp file" in text or "c# file" in text:
        ex = ".cs"

    elif "javascript file" in text:
        ex = ".js"

    elif "html file" in text:
        ex = ".html"

    elif "css file" in text:
        ex = ".css"

    elif "php file" in text:
        ex = ".php"

    elif "ruby file" in text:
        ex = ".rb"

    elif "go file" in text:
        ex = ".go"

    elif "swift file" in text:
        ex = ".swift"

    elif "kotlin file" in text:
        ex = ".kt"

    elif "typescript file" in text:
        ex = ".ts"


# Text & Documents

    elif "text file" in text:
        ex = ".txt"

    elif "pdf file" in text:
        ex = ".pdf"

    elif "word file" in text:
        ex = ".docx"

    elif "excel file" in text:
        ex = ".xlsx"

    elif "powerpoint file" in text:
        ex = ".pptx"

    elif "csv file" in text:
        ex = ".csv"

    elif "json file" in text:
        ex = ".json"

    elif "xml file" in text:
        ex = ".xml"


# Images

    elif "png file" in text:
        ex = ".png"

    elif "jpg file" in text or "jpeg file" in text:
        ex = ".jpg"

    elif "gif file" in text:
        ex = ".gif"

    elif "bmp file" in text:
        ex = ".bmp"


# Audio

    elif "mp3 file" in text:
        ex = ".mp3"

    elif "wav file" in text:
        ex = ".wav"

    elif "audio file" in text:
        ex = ".mp3"


# Video

    elif "mp4 file" in text:
        ex = ".mp4"

    elif "mkv file" in text:
        ex = ".mkv"

    elif "video file" in text:
        ex = ".mp4"


# Other useful

    elif "zip file" in text:
        ex = ".zip"

    elif "rar file" in text:
        ex = ".rar"

    elif "exe file" in text:
        ex = ".exe"

    else:
        ex = ""
    return ex

def update_text(text):
    if "python file" in text:
        text = text.replace("python file", "")

    elif "java file" in text:
        text = text.replace("java file", "")

    elif "c file" in text:
        text = text.replace("c file", "")

    elif "c plus plus file" in text:
        text = text.replace("c plus plus file", "")

    elif "cpp file" in text:
        text = text.replace("cpp file", "")

    elif "c sharp file" in text:
        text = text.replace("c sharp file", "")

    elif "c# file" in text:
        text = text.replace("c# file", "")

    elif "javascript file" in text:
        text = text.replace("javascript file", "")

    elif "html file" in text:
        text = text.replace("html file", "")

    elif "css file" in text:
        text = text.replace("css file", "")

    elif "php file" in text:
        text = text.replace("php file", "")

    elif "ruby file" in text:
        text = text.replace("ruby file", "")

    elif "go file" in text:
        text = text.replace("go file", "")

    elif "swift file" in text:
        text = text.replace("swift file", "")

    elif "kotlin file" in text:
        text = text.replace("kotlin file", "")

    elif "typescript file" in text:
        text = text.replace("typescript file", "")

    # Documents

    elif "text file" in text:
        text = text.replace("text file", "")

    elif "pdf file" in text:
        text = text.replace("pdf file", "")

    elif "word file" in text:
        text = text.replace("word file", "")

    elif "excel file" in text:
        text = text.replace("excel file", "")

    elif "powerpoint file" in text:
        text = text.replace("powerpoint file", "")

    elif "csv file" in text:
        text = text.replace("csv file", "")

    elif "json file" in text:
        text = text.replace("json file", "")

    elif "xml file" in text:
        text = text.replace("xml file", "")

    # Images

    elif "png file" in text:
        text = text.replace("png file", "")

    elif "jpg file" in text:
        text = text.replace("jpg file", "")

    elif "jpeg file" in text:
        text = text.replace("jpeg file", "")

    elif "gif file" in text:
        text = text.replace("gif file", "")

    elif "bmp file" in text:
        text = text.replace("bmp file", "")

    # Audio

    elif "mp3 file" in text:
        text = text.replace("mp3 file", "")

    elif "wav file" in text:
        text = text.replace("wav file", "")

    elif "audio file" in text:
        text = text.replace("audio file", "")

    # Video

    elif "mp4 file" in text:
        text = text.replace("mp4 file", "")

    elif "mkv file" in text:
        text = text.replace("mkv file", "")

    elif "video file" in text:
        text = text.replace("video file", "")

    # Other

    elif "zip file" in text:
        text = text.replace("zip file", "")

    elif "rar file" in text:
        text = text.replace("rar file", "")

    elif "exe file" in text:
        text = text.replace("exe file", "")
    else:
        pass

    return text



def create_file(text):
    selected_ex = get_file_extension(text)
    text = update_text(text)
    if "named" in text or "with name" in text:
        text = text.replace("named","")
        text = text.replace("with named","")
        text = text.replace("create","")
        text = text.strip()
        with open(f"{text}{selected_ex}","w"):
            pass
    else:
        with open(f"demo{selected_ex}","w"):
            pass
