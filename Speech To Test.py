import whisper

model = whisper.load_model("large-v2")

result = model.transcribe(audio = "audios/12_Exercise 1 - Pure HTML Media Player.mp3", 
                          language="hi",
                          task="translate" )

print(result["text"])