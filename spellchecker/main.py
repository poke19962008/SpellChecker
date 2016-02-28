import LevenshteinDistance as LD
import re, pymongo

class SpellChecker:
    def __init__(self):
        try:
            con = pymongo.Connection(host="mongodb://localhost:27017/spellchecker", port=27017)
            print "Connected to MongoDB"
        except:
            print "[ERROR] Cannot connect to MongoDB"

        self.db = con['spellchecker']

        LD.compute('cook', 'books')

    def train(self):
        corpus = open('spellchecker/corpus.txt').read()

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
                self.db.dictionary.insert(data)
                counter = counter + 1
            except:
                print "[ERROR] Cannot insert " + data['word']

        print "[SUCCESS] Inserted " + str(counter) + " of " + str(len(corpus.split('\n')))

    def correct(self, wrongWord):
        closestMatch = []
        level = 1
        words = self.db.dictionary.find({}, {'_id': False, 'word': True})[:10]

        parents = [{'word': wrongWord, 'minLD': None}];

        while level<3:
            frontier = []
            for parent in parents:
                minLD = 1000
                matches = {}

                for wordDic in words:
                    word = wordDic['word']
                    editDistance = LD.compute(parent['word'], word)

                    minLD = min(minLD, editDistance)

                    if(not matches.has_key(editDistance)):
                        matches[editDistance] = []
                    matches[editDistance].append(word)
                    frontier.append({'word': word, 'minLD': None})

                closestMatch.append({'words': matches[minLD]})
            parents = frontier
            level = level + 1
