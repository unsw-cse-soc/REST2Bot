import werkzeug
from flask import Flask, jsonify, request
from flask_restplus import Api, Resource, reqparse, abort, fields, inputs, Model

from canonical.api2can_gen import TrainingExprGenerator
from canonical.rule_based import RuleBasedCanonicalGenerator
from paraphrase.paraphrasers import Paraphraser, PARAPHRASERS
from swagger.entities import Operation, Param, IntentCanonical
from swagger.swagger_analysis import SwaggerAnalyser

app = Flask(__name__)
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
paraphraser_parser.add_argument('n', type=int, help="number of paraphrases", location='args')
paraphraser_parser.add_argument('paraphrasers', type=str,
                                help='Pick from: {}'.format(", ".join(PARAPHRASERS)),
                                action="append", location='args')


@api.route("/extract_operations")
class Specs(Resource):
    @api.expect(yaml_parser)
    @api.response(200, "Success", [operation_model])
    def post(self):
        """
        extracts operations of a given swagger specs
        """
        if "yaml" not in request.files:
            abort(401, message="file is missing")
        try:
            yaml = request.files['yaml'].stream.read().decode("utf-8")
            doc = SwaggerAnalyser(swagger=yaml).analyse()
            ret = [a.to_json() for a in doc]
            return jsonify(ret)
        except Exception as e:
            print(e)
            abort(501, message="Server is not able to process the request")


@api.route("/generate_canonicals")
class Canonicals(Resource):
    @api.expect([operation_model])
    @api.response(200, "Success", [canonical_model])
    def post(self):
        """
        generates canonical sentences for a list of operations
        """
        try:
            ret = []
            lst = request.json
            for o in lst:
                operation = Operation.from_json(o)
                canonicals = expr_gen.to_canonical(operation, ignore_non_path_params=False)
                if canonicals:
                    ret.extend(canonicals)
                canonicals = rule_gen.translate(operation, sample_values=False, ignore_non_path_params=False)
                if canonicals:
                    ret.extend(canonicals)

            return jsonify([a.to_json() for a in ret])
        except Exception as e:
            print(e)
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
            n = args.get("n")
            if not n:
                n = 10

            paraphrasers = args.get("paraphrasers")
            canonicals = request.json

            ret = []
            for c in canonicals:
                c = IntentCanonical.from_json(c)
                c.paraphrases = paraphraser.paraphrase(c.canonical, c.entities, n,
                                                       paraphrasers if paraphrasers else None)
                ret.append(c.to_json())

            return jsonify(ret)

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
    app.run("0.0.0.0", port=8080)
