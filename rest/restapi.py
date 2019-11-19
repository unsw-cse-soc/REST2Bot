import logging
import werkzeug
from flask import Flask, jsonify, request
from flask_restplus import Api, Resource, reqparse, abort, fields, inputs, Model

from canonical.api2can_gen import TrainingExprGenerator
from canonical.rule_based import RuleBasedCanonicalGenerator
from paraphrase.paraphrasers import Paraphraser, PARAPHRASERS
from swagger.entities import Operation, Param, IntentCanonical
from swagger.swagger_analysis import SwaggerAnalyser
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
api = Api(app,
          default="APIs",
          title="REST2Bot APIs",
          description="A collection of APIs to automate bot development")

param_model = api.model('Parameter', {
    "name": fields.String,
    "type": fields.String,
    "desc": fields.String,
    "example": fields.String,
    "required": fields.Boolean,
    "is_auth_param": fields.Boolean,
})

paraphrase_model = api.model('Paraphrase', {
    "text": fields.String,
    "method": fields.String,
    "score": fields.Integer,
    "entities": fields.List(fields.Nested(param_model)),
})

canonical_paraphrase_model = api.model('Canonical Paraphrases', {
    "intent": fields.String,
    "canonical": fields.String,
    # "entities": fields.List(fields.Nested(param_model)),
    "paraphrases": fields.List(fields.Nested(paraphrase_model)),

})

canonical_model = api.model('IntentCanonicals', {
    "intent": fields.String,
    "canonical": fields.String,
    "entities": fields.List(fields.Nested(param_model)),
    # "paraphrases": fields.List(fields.Nested(paraphrase_model)),
})

operation_model = api.model('Operation', {
    "base_path": fields.String,
    "verb": fields.String,
    "url": fields.String,
    "intent": fields.String,
    "summary": fields.String,
    "desc": fields.String,
    "canonical": fields.String,
    "params": fields.List(fields.Nested(param_model)),
})

expr_gen = TrainingExprGenerator()
rule_gen = RuleBasedCanonicalGenerator()
paraphraser = Paraphraser()

yaml_parser = reqparse.RequestParser()
yaml_parser.add_argument('yaml', type=werkzeug.datastructures.FileStorage, location='files', required=True)

query_parser = reqparse.RequestParser()
query_parser.add_argument('n', type=int, help="number of sampled values for the given entity")

paraphraser_parser = reqparse.RequestParser()
paraphraser_parser.add_argument('params', type=int, help="number of sampled values for each entities", location='args')
paraphraser_parser.add_argument('count', type=int, help="number of paraphrases", location='args')
paraphraser_parser.add_argument('score', type=inputs.boolean, default=False, help="score generated paraphrases",
                                location='args')
paraphraser_parser.add_argument('paraphrasers', type=str,
                                help='Pick from: {}'.format(", ".join(PARAPHRASERS)),
                                action="append", location='args')


TRANSLATORS = {
    "RULE",
    "SUMMARY",
    "NEURAL"
}
canonical_parser = reqparse.RequestParser()
canonical_parser.add_argument('translators', type=str,
                                help='Pick from: {}'.format(", ".join(TRANSLATORS)),
                                action="append", location='args')


@api.route("/extract_operations")
class Specs(Resource):
    @api.expect(yaml_parser)
    @api.response(200, "Success", [operation_model])
    def post(self):
        """
        extracts operations of a given swagger specs
        """
        files = list(request.files.values())
        if not files:
            abort(401, message="file is missing")
        try:
            ret = []
            for file in files:
                yaml = file.stream.read().decode("utf-8")
                doc = SwaggerAnalyser(swagger=yaml).analyse()
                ret.extend([a.to_json() for a in doc])

            ret = {
                "operations": ret,
                "success": True,
            }
            return jsonify(ret)
        except Exception as e:
            print(e)
            abort(501, message="Server is not able to process the request")


@api.route("/generate_canonicals")
class Canonicals(Resource):
    @api.expect(canonical_parser, [operation_model])
    @api.response(200, "Success", [canonical_model])
    def post(self):
        """
        generates canonical sentences for a list of operations
        """
        try:
            ret = []
            args = canonical_parser.parse_args()
            translators = args.get("translators", TRANSLATORS)
            lst = request.json
            for o in lst:
                operation = Operation.from_json(o)
                if not translators or "SUMMARY" in translators:
                    canonicals = expr_gen.to_canonical(operation, ignore_non_path_params=False)

                    if canonicals:
                        ret.extend(canonicals)

                if not translators or "RULE" in translators:
                    canonicals = rule_gen.translate(operation, sample_values=False, ignore_non_path_params=False)
                    if canonicals:
                        ret.extend(canonicals)

            return jsonify([a.to_json() for a in ret])
        except Exception as e:
            print(e)
            raise e
            abort(400, message=e)


@api.route("/generate_paraphrases")
class Paraphrases(Resource):
    @api.expect(paraphraser_parser, [fields.Nested(canonical_model)])
    @api.response(200, "Success", [canonical_paraphrase_model])
    def post(self):
        """
        generates paraphrases for a given sentence
        """
        try:

            args = paraphraser_parser.parse_args()
            n = args.get("params", 10)
            count = args.get("count", 10)
            paraphrasers = args.get("paraphrasers", [])
            score = args.get("score", True)
            canonicals = request.json

            ret = []
            for c in canonicals:
                c = IntentCanonical.from_json(c)
                c.paraphrases = paraphraser.paraphrase(c.canonical, c.entities, count, n,
                                                       paraphrasers if paraphrasers else None,
                                                       score)
                ret.append(c.to_json())

            return jsonify(ret[:n])

        except Exception as e:
            raise e
            abort(400, message=e)


@api.route("/suggest_parameter_values")
class EntityValues(Resource):
    @api.expect(param_model, query_parser)
    def post(self):
        """
        generates sample values for the given parameter
        """
        try:
            args = query_parser.parse_args()
            n = args.get("n")
            if not n:
                n = 10
            param = Param.from_json(request.json)

            ret = paraphraser.param_sampler.sample(param, n)
            return jsonify(ret)

        except Exception as e:
            print(e)
            abort(400, message=e)


if __name__ == '__main__':
    LOGGER = logging.getLogger("artemis.fileman.disk_memoize")
    LOGGER.setLevel(logging.WARN)
    app.run("0.0.0.0", port=8080)
