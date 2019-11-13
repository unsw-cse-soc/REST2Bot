import requests


def joshua_paraphrase(sentence):
    data = requests.get("http://localhost:5674/translate?q=" + sentence)

    try:
        return [p['hyp'] for p in data.json()['data']['translations'][0]['raw_nbest']]
    except:
        return []


