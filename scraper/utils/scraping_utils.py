def identify_song_type(song_icon_src: str) -> str:
    if song_icon_src.__contains__("music_dx.png"):
        return "dx"
    elif song_icon_src.__contains__("music_standard.png"):
        return "standard"
    else:
        return "unknown"
