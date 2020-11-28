# REST2Bot

You can run "canonical utterance generator" as a service:
- Download "stanford-corenlp-full-2018-10-05" and unzip it in the root directory of the project
- Run the service as follow
```bash
pip3 install -r requirements.txt
cd REST3Bot\rest
python3 restapi.py
```
## More information
For more information please refer to the following papars:
```sh
@inproceedings{api2can_edbt_2020,
  title={Automatic Canonical Utterance Generation for Task-OrientedBots from API Specifications},
  author={Yaghoubzadeh, Mohammadali and Benatallah, Boualem, and Zamanirad, Shayan},
  booktitle={Advances in Database Technology-23rd International Conference on Extending Database Technology (EDBT)},
  year={2020}
}

@inproceedings{rest2bot_www_2020,
    author = {Yaghoub-Zadeh-Fard, Mohammad-Ali and Zamanirad, Shayan and Benatallah, Boualem and Casati, Fabio},
    title = {REST2Bot: Bridging the Gap between Bot Platforms and REST APIs},
    year = {2020},
    isbn = {9781450370240},
    publisher = {Association for Computing Machinery},
    address = {New York, NY, USA},
    url = {https://doi.org/10.1145/3366424.3383551},
    doi = {10.1145/3366424.3383551},
    booktitle = {Companion Proceedings of the Web Conference 2020},
    pages = {245–248},
    numpages = {4},
    keywords = {Paraphrasing, Chatbots, Automated Bot Development, REST APIs},
    location = {Taipei, Taiwan},
    series = {WWW ’20}
}
```

