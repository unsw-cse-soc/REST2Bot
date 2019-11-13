from swagger.entities import Paraphrase
from swagger.param_sampling import ParamValueSampler


class ParamValParaphraser:
    def __init__(self, param_sampler: ParamValueSampler) -> None:
        self.param_sampler = param_sampler

    def paraphrase(self, paraphrases: list, params: list, n: int) -> list:
        valid_uttrs = []

        if not params:
            return paraphrases

        cparams = [p.clone() for p in params]
        ret = []
        for paraph in paraphrases:
            all_params = True

            if "<<" not in paraph.paraphrase:
                ret.append(paraph)
                continue

            for p in cparams:
                if "<< {} >>".format(p.name) not in paraph.paraphrase:
                    all_params = False
                    break
            if all_params:
                valid_uttrs.append(paraph)

        for p in params:
            values = self.param_sampler.sample(p, n)
            pname = "<< {} >>".format(p.name)
            new_utter = []
            for v in values:
                for paraph in valid_uttrs:
                    # paraph = t[0]
                    # ps = t[1]
                    paraph.paraphrase = paraph.paraphrase.replace(pname, str(v))
                    paraph.entities = [p.clone() for p in paraph.entities]
                    for c in paraph.entities:
                        if c.name == p.name:
                            c.example = v

                    # if new_u not in allset:
                    new_utter.append(p)

            ret.extend(new_utter)
        return ret
