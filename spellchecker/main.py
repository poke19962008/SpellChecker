import LevenshteinDistance as LD
import re, pymongo

class SpellChecker:
    def __init__(self):
        LD.compute('hello', 'start')

    def train(self):
        corpus = open('spellchecker/corpus.txt').read()

        try:
            con = pymongo.Connection(host="mongodb://localhost:27017/spellchecker", port=27017)
            print "Connected to MongoDB"
        except:
            print "[ERROR] Cannot connect to MongoDB"

        db = con['spellchecker']
        counter = 0
        print "Started inserting in Mongo"
        for row in corpus.split('\n'):
            data = {}
            row = row.split('\t')

            data['rank'] = row[0]
            data['word'] = re.sub(r"\s{3}", "", row[1])
            data['frequency'] = row[3]
            data['dispersion'] = row[4]

            try:
                db.dictionary.insert(data)
                counter = counter + 1
            except:
                print "[ERROR] Cannot insert " + data['word']

        print "[SUCCESS] Inserted " + str(counter) + " of " + str(len(corpus.split('\n')))
