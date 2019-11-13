from paraphrase.common_prefix import PrefixParaphraser
from paraphrase.parameter_replacement import ParamValParaphraser
from swagger.entities import Param, Paraphrase
from swagger.param_sampling import ParamValueSampler
from utils.joshua import joshua_paraphrase
from utils.nematus import NematusParaphraseGenerator
from utils.sentence_embeddings import similarity

PARAPHRASERS = [
    'COMMON_PREFIX'
    'APACHE_JOSHUA',
    'NEMATUS'
]


def similarity_score(utterance, ps):
    for p in ps:
        p.score = similarity(utterance, p.paraphrase, "UniversalSentenceEncoder")
    ps = sorted(ps, key=lambda p: - p.score)
    return ps


class Paraphraser:
    def __init__(self) -> None:
        self.cp = PrefixParaphraser()
        self.param_sampler = ParamValueSampler()
        self.nematus = NematusParaphraseGenerator()
        self.paramValParaphraser = ParamValParaphraser(param_sampler=self.param_sampler)

    def paraphrase(self, utterance, params: list, num_of_sampled_params=100, paraphrasers=PARAPHRASERS, score=True):

        ps = []
        if not paraphrasers or 'COMMON_PREFIX' in paraphrasers:
            ps.extend(createParaphrase(self.cp.paraphrase(utterance), params, 'COMMON_PREFIX'))

        if not paraphrasers or 'APACHE_JOSHUA' in paraphrasers:
            ps.extend(createParaphrase(joshua_paraphrase(utterance), params, 'APACHE_JOSHUA'))

        if not paraphrasers or 'NEMATUS' in paraphrasers:
            ps.extend(createParaphrase(self.nematus.paraphrase(utterance.split()), params, 'NEMATUS'))

        ps = self.paramValParaphraser.paraphrase(ps, params, num_of_sampled_params)

        if score:
            ps = similarity_score(utterance, ps)
        return ps


def createParaphrase(paraphrases, entities, method):
    ret = []

    for p in paraphrases:
        p = Paraphrase(p, entities)
        p.score = 0
        p.method = method
        ret.append(p)

    return ret


if __name__ == "__main__":
    for p in Paraphraser().paraphrase("get a customer with id 1", [Param("id", example=1)]):
        print(p)
