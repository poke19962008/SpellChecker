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
        level = 1

        parents = [{'word': wrongWord, 'edits': 0}]
        exceptions = []

        # Run till height=3
        while level <= 3:
            frontier = []
            for parent in parents:
                minLD = 1000
                matches = {}

                if level != 1:
                    words = self.db.dictionary.find({
                        'word': {
                                '$nin' : exceptions
                            }
                        }, {
                            '_id': False,
                            'word': True
                    })
                else:
                    words = self.db.dictionary.find({}, {
                            '_id': False,
                            'word': True
                    })

                for wordDic in words:

                    # Calcuate minimum edit distance of one Level
                    word = wordDic['word']
                    editDistance = LD.compute(parent['word'], word)
                    minLD = min(minLD, editDistance)

                    if(not matches.has_key(editDistance)):
                        matches[editDistance] = []
                    matches[editDistance].append(word)

                if minLD != 1000:
                    closestMatch.append({'words': matches[minLD], 'graphDepth': level, 'edits': minLD, 'parent': parent['word']})

                    # Add exception and frontiers with best matches
                    for x in matches[minLD]:
                        exceptions.append(x)
                        frontier.append({'word': x, 'edits': editDistance})
            parents = frontier
            level = level + 1
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
        corpus = open('spellchecker/corpus.txt').read()

        counter = 0
        print "Started inserting in Mongo"
        for row in corpus.split('\n'):
            data = {}
            row = row.split('\t')

            data['rank'] = row[0]
            data['word'] = re.sub(r"\s{3}", "", row[1]).lower()
            data['frequency'] = row[3]
            data['dispersion'] = row[4]

            try:
                self.db.dictionary.insert(data)
                counter = counter + 1
            except:
                print "[ERROR] Cannot insert " + data['word']

        print "[SUCCESS] Inserted " + str(counter) + " of " + str(len(corpus.split('\n')))

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
