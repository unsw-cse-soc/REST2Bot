from paraphrase.common_prefix import PrefixParaphraser
from paraphrase.parameter_replacement import ParamValParaphraser
from swagger.entities import Param, Paraphrase
from swagger.param_sampling import ParamValueSampler
from utils.joshua import joshua_paraphrase
from utils.nematus import NematusParaphraseGenerator

PARAPHRASERS = [
    'COMMON_PREFIX'
    'APACHE_JOSHUA',
    'NEMATUS'
]


class Paraphraser:
    def __init__(self) -> None:
        self.cp = PrefixParaphraser()
        self.param_sampler = ParamValueSampler()
        self.nematus = NematusParaphraseGenerator()
        self.paramValParaphraser = ParamValParaphraser(param_sampler=self.param_sampler)

    def paraphrase(self, utterance, params: list, num_of_sampled_params=100, paraphrasers=PARAPHRASERS):

        ps = []
        if 'COMMON_PREFIX' in paraphrasers:
            ps.extend(createParaphrase(self.cp.paraphrase(utterance), params, 'COMMON_PREFIX'))

        if 'APACHE_JOSHUA' in paraphrasers:
            ps.extend(createParaphrase(joshua_paraphrase(utterance), params, 'APACHE_JOSHUA'))

        if 'NEMATUS' in paraphrasers:
            ps.extend(createParaphrase(self.nematus.paraphrase(utterance.split()), params, 'NEMATUS'))

        ps = self.paramValParaphraser.paraphrase(ps, params, num_of_sampled_params)
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
