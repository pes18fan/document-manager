# Document categorizer thing

- get ocr working
- get image preprocessor working
- get keyword grabbing working

# Scrapped ideas

## Nepali Transcription-er -> Romanized

- use a speech to text model supporting Nepali for transcribing
    - OpenAI Whisper or Meta's MMS seem good for this purpose
- finetune it; there's a bunch of audio available for finetuning around
- also add other audio to give it broader sources and stuff
- either train it on Colab or use RIU or something idk

- for the romanization you can use existing deterministic rules
- add some extra modifications to make it look more natural
    - for instance remove the diacritics, drop schwas, et cetera
