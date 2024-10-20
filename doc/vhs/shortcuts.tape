# VHS documentation
#
# Output:
#   Output <path>.gif               Create a GIF output at the given <path>
#   Output <path>.mp4               Create an MP4 output at the given <path>
#   Output <path>.webm              Create a WebM output at the given <path>
#
# Settings:
#   Set FontSize <number>           Set the font size of the terminal
#   Set FontFamily <string>         Set the font family of the terminal
#   Set Height <number>             Set the height of the terminal
#   Set Width <number>              Set the width of the terminal
#   Set LetterSpacing <float>       Set the font letter spacing (tracking)
#   Set LineHeight <float>          Set the font line height
#   Set Theme <string>              Set the theme of the terminal (JSON)
#   Set Padding <number>            Set the padding of the terminal
#   Set Framerate <number>          Set the framerate of the recording
#   Set PlaybackSpeed <float>       Set the playback speed of the recording
#
# Sleep:
#   Sleep <time>                    Sleep for a set amount of <time> in seconds
#
# Type:
#   Type[@<time>] "<characters>"    Type <characters> into the terminal with a
#                                   <time> delay between each character
#
# Keys:
#   Backspace[@<time>] [number]     Press the Backspace key
#   Down[@<time>] [number]          Press the Down key
#   Enter[@<time>] [number]         Press the Enter key
#   Space[@<time>] [number]         Press the Space key
#   Tab[@<time>] [number]           Press the Tab key
#   Left[@<time>] [number]          Press the Left Arrow key
#   Right[@<time>] [number]         Press the Right Arrow key
#   Up[@<time>] [number]            Press the Up Arrow key
#   Down[@<time>] [number]          Press the Down Arrow key
#   Ctrl+<key>                      Press the Control key + <key> (e.g. Ctrl+C)
#
# Display:
#   Hide                            Hide the subsequent commands from the output
#   Show                            Show the subsequent commands in the output

Output shortcuts.gif

Set FontSize 36
Set Width 1600
Set Height 800
Set Padding 40
Set PlaybackSpeed 0.5
# Set Theme "Catppuccin Frappe"
Set Theme {"name":"Catppuccin Frappe","black":"#51576d","red":"#e78284","green":"#a6d189","yellow":"#e5c890","blue":"#8caaee","magenta":"#f4b8e4","cyan":"#81c8be","white":"#b5bfe2","brightBlack":"#626880","brightRed":"#e78284","brightGreen":"#a6d189","brightYellow":"#e5c890","brightBlue":"#8caaee","brightMagenta":"#f4b8e4","brightCyan":"#81c8be","brightWhite":"#a5adce","background":"#303446","foreground":"#c6d0f5","selection":"#626880","cursor":"#f2d5cf"}

Type "papis browse" Sleep 500ms Enter

Sleep 1s

Ctrl+e Sleep 1s

Type ":wq" Sleep 500ms Enter

Sleep 1s
