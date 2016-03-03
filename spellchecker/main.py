__author__ = "SAYAN DAS"

import LevenshteinDistance as LD
import re, pymongo, operator

class SpellChecker:
    def __init__(self):
        try:
            con = pymongo.Connection(host="mongodb://localhost:27017/spellchecker", port=27017)
        except:
            print "[ERROR] Cannot connect to MongoDB"

        self.db = con['spellchecker']

    '''
        Generate BK-Tree with mispelled word as top node
    '''
    def _genTree(self, wrongWord):
        closestMatch = []

        # Level 1:
        words =  self.db.dictionary.find({}, {
             '_id': False,
             'word': True
        })

        minED = 1000
        data = {}
        for wordDict in words:
            word = wordDict['word']

            editDistance = LD.compute(wrongWord, word)
            minED = min(minED, editDistance)

            if not data.has_key(editDistance):
                data[editDistance] = {}
                data[editDistance]['word'] = []
            data[editDistance]['word'].append(word)

        parent = [{
            'graphDepth': 1,
            'parent': wrongWord,
            'edits': minED,
            'words': data[minED]['word']
        }]
        closestMatch = [parent[0]]
        Level = 2
        while Level <= 3:

            for tuple_ in parent:
                frontier = []
                parent = tuple_['parent']
                words = tuple_['words']
                for word in words:
                    match = self.db.tree.find_one({'parent': word})
                    frontier.append({
                        'graphDepth': Level,
                        'parent': word,
                        'edits': match['edits'],
                        'words': match['words']
                    })
                    closestMatch.append(frontier[-1])

            Level = Level + 1
            parent = frontier
        return closestMatch

    '''
        Assigns rank on the basis of graphDepth, frequency, edit distance
    '''
    def _rank(self, matches):
        wordDet = {}
        rank = {}
        for match in matches:
            for word in match['words']:

                # Calculate total edits
                if match['graphDepth'] == 1:
                    wordDet[word] = {
                        'edits': match['edits']
                    }
                elif match['graphDepth'] == 2:
                    previousEdit = wordDet[match['parent']]['edits']
                    wordDet[word] = {
                        'edits': match['edits'] + previousEdit
                    }
                else:
                    previousEdit = wordDet[match['parent']]['edits']
                    wordDet[word] = {
                        'edits': match['edits'] + previousEdit
                    }

                # Calculate frequency probability and depth score
                freqRank =  self.db.dictionary.find_one({
                    'word': word
                },{
                    'rank': True,
                    '_id': False
                })['rank']

                wordDet[word]['depthScore'] = 3/float(match['graphDepth'])
                wordDet[word]['freqProb'] = 1/float(freqRank)

                value = wordDet[word]
                score = value['depthScore'] + value['freqProb']
                if value['edits'] != 0:
                    score = score + 1/value['edits']
                else:
                    score = score + 1000
                rank[word] = score

        rank = sorted(rank.items(), key=operator.itemgetter(1), reverse=True)

        print "\n\nWord Detailed Score: "
        for key in wordDet:
            print key, ": ", wordDet[key]

        print "\n\nScore Card for %s : " % (self.wrongWord)
        counter = 5
        for x in rank:
            print x
            if counter == 0:
                break
            else:
                counter = counter -1

        return rank

    '''
        Insert docs in Mongo(NoSQL Database)
    '''
    def train(self):
        counter = 0

        print "Inserting words in dictionary"
        corpus = open('spellchecker/corpus.txt').read()
        dictionary = []
        for row in corpus.split('\n'):
            data = {}

            row = row.split('\t')

            data['rank'] = row[0]
            data['word'] = re.sub(r"\s{3}", "", row[1]).lower()
            data['frequency'] = row[3]
            data['dispersion'] = row[4]

            dictionary.append(data)
            try:
                self.db.dictionary.insert(data)
                counter = counter + 1
            except:
                print "[ERROR] Cannot insert " + data['word']

        print "[SUCCESS] Inserted " + str(counter) + "/5000 words in `dictionary` collection"

        counter = 0
        print "Generating Level-1 BK-Tree of each word."
        for wordD in dictionary:
            parent = wordD['word']
            tmp = {}
            minEdit = 1000
            for wordD in dictionary:
                value = wordD['word']

                if value == parent:
                    continue
                ed = LD.compute(parent, value)
                if not tmp.has_key(ed):
                    tmp[ed] = {}
                    tmp[ed]['words'] = []
                tmp[ed]['words'].append(value)

                minEdit = min(minEdit, ed)

            tmp[minEdit]['edits'] = minEdit
            data = {
                'parent': parent,
                'edits': minEdit,
                'words': tmp[minEdit]['words']
            }

            try:
                self.db.tree.insert(data)
                counter = counter + 1
                print "[SUCCESS] " + parent + " done with " + str(len(tmp[minEdit]['words'])) + " children"
            except:
                print "[ERROR] Cannot insert " + data['parent']

        print "[SUCCESS] Inserted " + str(counter) + "/5000 words in `dictionary` collection"

    '''
        Genrates Tree and creates rank list
    '''
    def correct(self, wrongWord):
        self.wrongWord = wrongWord
        matches = self._genTree(wrongWord)

        print "\nPossible Matches (BK-Tree): "
        for foo in matches:
            print foo

        self._rank(matches)
