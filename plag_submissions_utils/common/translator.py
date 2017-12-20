import sys
import requests
import json
import urllib
from googletrans import Translator


class YaGoTrans:
    def __init__(self, api_key):
        self.api_key = api_key
        self.google_trans = Translator()

    def error(self, message, status_code):
        sys.stderr.write(message + '\n')
        sys.stderr.write('Status code: {0}\n'.format(status_code))

    def translate(self, text, translator='yandex', dest_lang='ru', encoding='utf-8'):
        if translator == 'google':
            return self.google_trans.translate(text, dest=dest_lang).text.encode(encoding)
        textFromInput = text

        urlDetectLanguage = 'https://translate.yandex.net/api/v1.5/tr.json/detect?key={0}&text={1}'
        urlTranslate = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key={0}&lang={1}&text={2}'

        requestDetectLanguage = requests.post(urlDetectLanguage.format(self.api_key, urllib.quote(textFromInput)))

        if requestDetectLanguage.status_code == 200:
            detectedLanguage = json.loads(requestDetectLanguage.text)['lang']
            langPair = ''

            if detectedLanguage == dest_lang:
                langPair = dest_lang + '-en'
            else:
                langPair = detectedLanguage + '-' + dest_lang

            requestTranslate = requests.post(urlTranslate.format(self.api_key, langPair, urllib.quote(textFromInput)))

            if requestTranslate.status_code == 200:
                translatedText = ''.join(json.loads(requestTranslate.text)['text'])
                return translatedText.encode('utf-8')
            else:
                self.error('Error with translating', requestTranslate.status_code)
        else:
            self.error('Error with language detect', requestDetectLanguage.status_code)
