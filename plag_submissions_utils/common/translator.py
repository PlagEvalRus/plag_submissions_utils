import sys
import requests
import json
import urllib
from googletrans import Translator
from os import path, environ

CONFIG = 'config.txt'
ENV_VAR = 'SUBMISSION_UTILS_TRANSLATOR_CONFIG'
SEARCH_RANGE = 3


class YaGoTrans:
    def __init__(self):
        self.api_key = self._open_api_key()
        self.google_trans = Translator()

    def _check_enviroment_variable(self):
        return environ.get(ENV_VAR)

    def _open_config(self, ups):
        file = []
        [file.append(up) for up in ['..']*ups]
        file.append(CONFIG)
        return self._read_file(path.join(*file))

    def _read_file(self, filepath):
        with open(filepath, 'r') as f:
            return f.read()

    def _open_api_key(self):
        env_var = self._check_enviroment_variable()
        if env_var:
            return self._read_file(env_var)
        for up in range(SEARCH_RANGE):
            try:
                api_key = self._open_config(up).split('\n')[0]
                return api_key
            except IOError:
                continue
        raise ValueError('No config file was found!')

    def error(self, message, status_code):
        sys.stderr.write(message + '\n')
        sys.stderr.write('Status code: {0}\n'.format(status_code))

    def translate(self, text, translator='yandex', dest_lang='ru', encoding='utf-8'):
        if translator == 'google':
            # try:
            return self.google_trans.translate(text, dest=dest_lang).text.encode(encoding)
            # except:
            #    raise ValueError('No Internet connection!')
        textFromInput = text.encode('utf8')

        urlDetectLanguage = 'https://translate.yandex.net/api/v1.5/tr.json/detect?key={0}&text={1}'
        urlTranslate = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key={0}&lang={1}&text={2}'

        # try:
        requestDetectLanguage = requests.post(urlDetectLanguage.format(self.api_key, urllib.quote(textFromInput)))
        # except:
        #    raise ValueError('No Internet connection!')

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
